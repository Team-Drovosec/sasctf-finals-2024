package com.mercial.use.prohibited.controller;

import com.mercial.use.prohibited.AppConfig;
import com.mercial.use.prohibited.domain.Client;
import com.mercial.use.prohibited.domain.User;
import com.mercial.use.prohibited.dto.*;
import com.mercial.use.prohibited.error.AuthError;
import com.mercial.use.prohibited.repository.ClientRepository;
import com.mercial.use.prohibited.repository.UserRepository;
import io.micronaut.core.annotation.Nullable;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpResponseFactory;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.MediaType;
import io.micronaut.http.annotation.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.micronaut.views.View;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.KeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.time.Instant;
import java.time.LocalDateTime;
import java.util.*;
import java.security.spec.PKCS8EncodedKeySpec;

@Controller
public class AuthController {
    private final UserRepository userRepository;
    private final ClientRepository clientRepository;
    private final TokenAuthService tokenAuthService;
    private final AppConfig appConfig;

    public AuthController(UserRepository userRepository, ClientRepository clientRepository) throws Exception {
        this.userRepository = userRepository;
        this.clientRepository = clientRepository;
        this.appConfig = new AppConfig();
        this.appConfig.setProfilePropertyKeys(Collections.singletonList(this.appConfig.getPublicTokenKey()));
        this.appConfig.getPlayerCertificateKeys().add(this.appConfig.getPublicTokenKey());
        this.tokenAuthService = new TokenAuthService(this.appConfig, clientRepository);
    }

    @Post(uris={"/auth/authenticate", "/authlib-injector/authserver/authenticate"})
    public HttpResponse<?> authenticate(@Body @Valid AuthenticateRequestDTO request) throws Exception {
        var username = request.getUsername();
        Optional<User> userRow = userRepository.findByUsername(username);
        if (userRow.isEmpty()) {
            return AuthError.invalidCredentialsBlob;
        }
        User user = userRow.get();

        if (!verifyPassword(request.getPassword(), user.getPasswordHash(), user.getPasswordSalt())) {
            return AuthError.invalidCredentialsBlob;
        }

        Client client = new Client(
                UUID.randomUUID().toString(),
                new String(generateRandomBytes(16), StandardCharsets.UTF_8),
                0,
                user
        );
        if (request.getClientToken() == null) {
            var clients = user.getClients();
            clients.add(client);
            user.setClients(clients);
        } else {
            var clientToken = request.getClientToken();
            boolean clientExists = false;
            var userClients = user.getClients();
            for (int i = 0; userClients != null && i < userClients.size(); i++) {
                if (Objects.equals(userClients.get(i).getClientToken(), clientToken)) {
                    clientExists = true;
                    userClients.get(i).setVersion(userClients.get(i).getVersion() + 1);
                    client = userClients.get(i);
                } else {
                    userClients.get(i).setVersion(userClients.get(i).getVersion() + 1);
                }
            }

            if (!clientExists) {
                client = new Client(
                        UUID.randomUUID().toString(),
                        new String(clientToken.getBytes(StandardCharsets.UTF_8), StandardCharsets.UTF_8),
                        0,
                        user
                );
                var clients = user.getClients();
                clients.add(client);
                user.setClients(clients);
            }
        }

        var id = UUIDToID(user.getUuid());

        ProfileDTO selectedProfile = null;
        List<ProfileDTO> availableProfiles = null;
        if (request.getAgent() != null) {
            selectedProfile = new ProfileDTO(id, user.getPlayerName());
            availableProfiles = Collections.singletonList(selectedProfile);
        }

        UserResponseDTO userResponse = null;
        if (request.getRequestUser()) {
            userResponse = new UserResponseDTO(
                    id,
                    Collections.singletonList(new UserPropertyDTO(
                            "preferredLanguage",
                            "English"
                    ))
            );
        }

        userRepository.update(user);
        var accessToken = this.tokenAuthService.makeAccessToken(client);
        var authenticateResponse = new AuthenticateResponseDTO(
                accessToken,
                client.getClientToken(),
                selectedProfile,
                availableProfiles,
                userResponse
        );
        return HttpResponse.ok(authenticateResponse);
    }

    @Post(uris={"/auth/validate", "/authlib-injector/authserver/validate"})
    public HttpResponse<?> validate(@Body @Valid ValidateRequestDTO request) {
        Client client = tokenAuthService.getClient(request.getAccessToken());
        if (client == null || !Objects.equals(request.getClientToken(), client.getClientToken())) {
            return HttpResponse.unauthorized();
        }
        return HttpResponse.noContent();
    }

    @Post(uris={"/auth/refresh", "/authlib-injector/authserver/refresh"})
    public HttpResponse<?> refresh(@Body @Valid RefreshRequestDTO request) throws Exception {
        Client client = tokenAuthService.getClient(request.getAccessToken());
        if (client == null || !Objects.equals(request.getClientToken(), client.getClientToken())) {
            return AuthError.invalidAccessTokenBlob;
        }

        User user = client.getUser();
        var id = UUIDToID(user.getUuid());
        ProfileDTO selectedProfile = new ProfileDTO(id, user.getPlayerName());
        List<ProfileDTO> availableProfiles = Collections.singletonList(selectedProfile);

        UserResponseDTO userResponse = null;
        if (request.getRequestUser()) {
            userResponse = new UserResponseDTO(
                    id,
                    Collections.singletonList(new UserPropertyDTO(
                            "preferredLanguage",
                            "English"
                    ))
            );
        }
        client.setVersion(client.getVersion() + 1);
        var accessToken = tokenAuthService.makeAccessToken(client);
        clientRepository.update(client);
        RefreshResponseDTO refreshResponse = new RefreshResponseDTO(
                accessToken,
                client.getClientToken(),
                selectedProfile,
                availableProfiles,
                userResponse
        );
        return HttpResponse.ok(refreshResponse);
    }

    @Post(uris={"/auth/signout", "/authlib-injector/authserver/signout"})
    public HttpResponse<?> signout(@Body @Valid SignoutRequestDTO request) throws Exception {
        var username = request.getUsername();
        Optional<User> userRow = userRepository.findByUsername(username);
        if (userRow.isEmpty()) {
            return AuthError.invalidCredentialsBlob;
        }
        User user = userRow.get();

        if (!verifyPassword(request.getPassword(), user.getPasswordHash(), user.getPasswordSalt())) {
            return AuthError.invalidCredentialsBlob;
        }

        List<Client> clients = clientRepository.findByUser(user);
        for (Client client : clients) {
            client.setVersion(client.getVersion() + 1);
        }
        clientRepository.updateAll(clients);
        return HttpResponse.noContent();
    }

    @Post(uris={"/auth/invalidate", "/authlib-injector/authserver/invalidate"})
    public HttpResponse<?> invalidate(@Body @Valid InvalidateRequestDTO request) {
        Client currentClient = tokenAuthService.getClient(request.getAccessToken());
        if (currentClient == null || !Objects.equals(request.getClientToken(), currentClient.getClientToken())) {
            return AuthError.invalidAccessTokenBlob;
        }
        List<Client> clients = clientRepository.findByUser(currentClient.getUser());
        for (Client client : clients) {
            client.setVersion(client.getVersion() + 1);
        }
        clientRepository.updateAll(clients);
        return HttpResponse.noContent();
    }

    @Post(uris={"/session/session/minecraft/join", "/authlib-injector/sessionserver/session/minecraft/join"})
    public HttpResponse<?> joinSession(@Body @Valid SessionJoinRequestDTO request) {
        Client currentClient = tokenAuthService.getClient(request.getAccessToken());
        if (currentClient == null) {
            return HttpResponseFactory.INSTANCE.status(HttpStatus.FORBIDDEN);
        } else {
            User user = currentClient.getUser();
            user.setServerId(request.getServerId());
            userRepository.update(user);
            return HttpResponse.noContent();
        }
    }

    @Get(uris={"/session/session/minecraft/hasJoined", "/authlib-injector/sessionserver/session/minecraft/hasJoined"})
    public HttpResponse<?> hasJoinedSession(@NotNull String username) throws Exception {
        Optional<User> userRow = userRepository.findByUsername(username);
        if (userRow.isEmpty()) {
            return HttpResponseFactory.INSTANCE.status(HttpStatus.FORBIDDEN);
        }
        User user = userRow.get();
        return HttpResponse.ok(getFullProfile(user, true));
    }

    @Get(uris={"/session/session/minecraft/profile/{id}", "/authlib-injector/sessionserver/session/minecraft/profile/{id}"})
    public HttpResponse<?> getProfile(
            @PathVariable String id,
            @Nullable @QueryValue(defaultValue = "true") Boolean unsigned
    ) throws Exception {
        var uuid = idToUUID(id);
        Optional<User> userRow = userRepository.findById(uuid);
        if (userRow.isEmpty()) {
            return HttpResponse.noContent();
        }
        User user = userRow.get();

        return HttpResponse.ok(getFullProfile(user, !unsigned));
    }

    @Get("/authlib-injector")
    public HttpResponse<?> authlibInjector() throws NoSuchAlgorithmException, InvalidKeySpecException {
        var links = new AuthlibInjectorLinksDTO(
                appConfig.getApiUrl() + "/register",
                appConfig.getApiUrl() + "/register"
        );
        var meta = new AuthlibInjectorMetaDTO(
                "Cocos2d",
                "3.7.3",
                links,
                "Badlands MGE 24/7 !add 5",
                true
        );
        List<String> signaturePublicKeys = new ArrayList<>();
        for (var key : appConfig.getProfilePropertyKeys()) {
            signaturePublicKeys.add(authlibInjectorSerializeKey(key));
        }
        var response = new AuthlibInjectorResponseDTO(
                meta,
                authlibInjectorSerializeKey(appConfig.getPublicTokenKey()),
                signaturePublicKeys,
                Collections.singletonList(appConfig.getApiUrl())
        );
        return HttpResponse.ok(response);
    }

    @Get(uris={"/services/publickeys", "/authlib-injector/minecraftservices/publickeys"})
    public HttpResponse<?> getPubKeys() throws NoSuchAlgorithmException, InvalidKeySpecException {
        List<SerializedKeyDTO> serializedProfilePropertyKeys = new ArrayList<>();
        List<SerializedKeyDTO> serializedPlayerCertificateKeys = new ArrayList<>();

        for (var key : appConfig.getProfilePropertyKeys()) {
            serializedProfilePropertyKeys.add(new SerializedKeyDTO(encodeKey(key)));
        }
        for (var key : appConfig.getPlayerCertificateKeys()) {
            serializedPlayerCertificateKeys.add(new SerializedKeyDTO(encodeKey(key)));
        }

        var response = new PublicKeysResponseDTO(
                serializedPlayerCertificateKeys,
                serializedProfilePropertyKeys
        );
        return HttpResponse.ok(response);
    }

    @Post(uri = "/register", consumes = MediaType.APPLICATION_FORM_URLENCODED)
    public HttpResponse<?> register(@Body @Valid UserRegisterDTO userRegister) throws NoSuchAlgorithmException, InvalidKeySpecException {
        var username = userRegister.getUsername();
        if (!userRepository.findByUsername(userRegister.getUsername()).isEmpty()) {
            var message = "Username already taken";
            return HttpResponse.redirect(URI.create("/register?error=" + URLEncoder.encode(message, StandardCharsets.UTF_8)));
        }
        if (!userRepository.findByPlayerName(userRegister.getPlayerName()).isEmpty()) {
            var message = "Player name already taken";
            return HttpResponse.redirect(URI.create("/register?error=" + URLEncoder.encode(message, StandardCharsets.UTF_8)));
        }
        var salt = generateSalt();
        var passwordHash = hashPassword(userRegister.getPassword(), salt);
        var user = new User(
                UUID.randomUUID().toString(),
                username,
                salt,
                passwordHash,
                null,
                userRegister.getPlayerName(),
                LocalDateTime.now()
        );
        userRepository.save(user);
        return HttpResponse.redirect(URI.create("/success"));
    }

    @Get("/register")
    @View("index")
    public void register_view() {
        return;
    }

    @Get("/success")
    @View("success")
    public void success_view() {
        return;
    }

    private String encodeKey(byte[] key) throws NoSuchAlgorithmException, InvalidKeySpecException {
        X509EncodedKeySpec spec = new X509EncodedKeySpec(key);
        KeyFactory keyFactory = KeyFactory.getInstance("RSA");
        PublicKey publicKey = keyFactory.generatePublic(spec);
        RSAPublicKey rsaPublicKey = (RSAPublicKey) publicKey;
        byte[] publicKeyDer = rsaPublicKey.getEncoded();
        if (publicKeyDer == null || publicKeyDer.length == 0) {
            throw new IllegalArgumentException("Broken key");
        }
        String base64PublicKey = Base64.getEncoder().encodeToString(publicKeyDer);
        return base64PublicKey;
    }

    private String authlibInjectorSerializeKey(byte[] key) throws NoSuchAlgorithmException, InvalidKeySpecException {
        X509EncodedKeySpec spec = new X509EncodedKeySpec(key);
        KeyFactory keyFactory = KeyFactory.getInstance("RSA");
        PublicKey publicKey = keyFactory.generatePublic(spec);

        try {
            byte[] pubDER = publicKey.getEncoded();
            if (pubDER == null || pubDER.length == 0) {
                throw new IllegalArgumentException("Broken PublicKey");
            }

            String pubBase64 = Base64.getMimeEncoder(64, new byte[]{'\n'}).encodeToString(pubDER);

            String pubPEM = "-----BEGIN PUBLIC KEY-----\n" +
                    pubBase64 +
                    "\n-----END PUBLIC KEY-----\n";

            return pubPEM;
        } catch (Exception e) {
            throw new IllegalArgumentException("Broken PublicKey");
        }
    }

    private SessionProfileResponseDTO getFullProfile(User user, Boolean sign) throws Exception {
        String id = UUIDToID(user.getUuid());
        Instant now = Instant.now();
        long unixNano = now.getEpochSecond() * 1_000_000_000L + now.getNano();
        TextureValueDTO texturesValue = new TextureValueDTO(
                unixNano,
                id,
                user.getPlayerName(),
                new TextureMapDTO()
        );
        ObjectMapper mapper = new ObjectMapper();
        byte[] texturesValueBlob = mapper.writeValueAsBytes(texturesValue);

        String texturesValueBase64 = Base64.getEncoder().encodeToString(texturesValueBlob);
        String signatureBase64 = null;
        if (sign) {
            byte[] signatureBytes = signSHA1(texturesValueBase64.getBytes(StandardCharsets.UTF_8));
            signatureBase64 = Base64.getEncoder().encodeToString(signatureBytes);
        }
        SessionProfilePropertyDTO sessionProfileProperty = new SessionProfilePropertyDTO(
                "textures",
                texturesValueBase64,
                signatureBase64
        );
        return new SessionProfileResponseDTO(
                id,
                user.getPlayerName(),
                Collections.singletonList(sessionProfileProperty)
        );
    }

    public byte[] signSHA1(byte[] plaintext) throws Exception {
        MessageDigest sha1 = MessageDigest.getInstance("SHA-1");
        byte[] hash = sha1.digest(plaintext);

        Signature signature = Signature.getInstance("SHA1withRSA");
        PKCS8EncodedKeySpec spec = new PKCS8EncodedKeySpec(appConfig.getPrivateTokenKey());
        KeyFactory kf = KeyFactory.getInstance("RSA");
        PrivateKey privateKey = kf.generatePrivate(spec);

        signature.initSign(privateKey);
        signature.update(hash);
        return signature.sign();
    }

    private String UUIDToID(String uuid_value) throws Exception {
        if (uuid_value.length() != 36) {
            throw new Exception("uuid error");
        }
        return uuid_value.replace("-", "");
    }

    public static String idToUUID(String id) {
        if (id == null) {
            throw new IllegalArgumentException("id is null");
        }

        if (id.length() != 32) {
            throw new IllegalArgumentException("invalid id");
        }

        StringBuilder uuidBuilder = new StringBuilder();
        uuidBuilder.append(id, 0, 8).append("-");
        uuidBuilder.append(id, 8, 12).append("-");
        uuidBuilder.append(id, 12, 16).append("-");
        uuidBuilder.append(id, 16, 20).append("-");
        uuidBuilder.append(id, 20, 32);

        return uuidBuilder.toString();
    }

    private static byte[] generateRandomBytes(int numBytes) {
        byte[] randomBytes = new byte[numBytes];
        SecureRandom secureRandom = new SecureRandom();
        secureRandom.nextBytes(randomBytes);
        return randomBytes;
    }

    public static byte[] generateSalt() {
        SecureRandom random = new SecureRandom();
        byte[] salt = new byte[16];
        random.nextBytes(salt);
        return salt;
    }

    public static byte[] hashPassword(String password, byte[] salt)
            throws NoSuchAlgorithmException, InvalidKeySpecException {
        KeySpec spec = new PBEKeySpec(password.toCharArray(), salt, 65536, 256);
        SecretKeyFactory factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
        return factory.generateSecret(spec).getEncoded();
    }

    public static boolean verifyPassword(String inputPassword, byte[] storedHash, byte[] storedSalt)
            throws NoSuchAlgorithmException, InvalidKeySpecException {
        byte[] inputHash = hashPassword(inputPassword, storedSalt);
        return slowEquals(storedHash, inputHash);
    }

    private static boolean slowEquals(byte[] a, byte[] b) {
        if (a == null || b == null) {
            return false;
        }
        int diff = a.length ^ b.length;
        for (int i = 0; i < a.length && i < b.length; i++) {
            diff |= a[i] ^ b[i];
        }
        return diff == 0;
    }
}
