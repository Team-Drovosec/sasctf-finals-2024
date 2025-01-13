package com.mercial.use.prohibited;

import org.bouncycastle.asn1.pkcs.PrivateKeyInfo;
import org.bouncycastle.openssl.PEMKeyPair;
import org.bouncycastle.openssl.PEMParser;
import org.bouncycastle.openssl.jcajce.JcaPEMKeyConverter;
import org.bouncycastle.openssl.jcajce.JcaPEMWriter;
import org.bouncycastle.openssl.jcajce.JcaPKCS8Generator;

import java.io.File;
import java.io.FileWriter;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.KeyFactory;
import java.security.KeyPairGenerator;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.interfaces.RSAPrivateCrtKey;
import java.security.spec.RSAPublicKeySpec;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;

public class AppConfig {
    private long tokenExpireSec;
    private byte[] privateTokenKey;
    private byte[] publicTokenKey;
    private List<byte[]> profilePropertyKeys;
    private List<byte[]> playerCertificateKeys;
    private final String apiUrl;

    private static final long DEFAULT_TOKEN_EXPIRE_SEC = 3600;
    private static final String PRIVATE_TOKEN_KEY_PATH = "keys/rsakey.pem";
    private static final String PUBLIC_TOKEN_KEY_PATH = "keys/rsapubkey.pem";
    private static final String DEFAULT_APP_URL = "http://localhost:8080";

    public AppConfig() throws Exception {
        this.tokenExpireSec = getEnvAsLong("TOKEN_EXPIRE_SEC", DEFAULT_TOKEN_EXPIRE_SEC);
        this.apiUrl = getEnvAsString("APP_URL", DEFAULT_APP_URL);
        this.playerCertificateKeys = new ArrayList<>();
        getOrCreatePrivateKey();
        getOrCreatePublicKey();

        String privateTokenKey64 = new String(privateTokenKey, StandardCharsets.UTF_8);;
        privateTokenKey64 = privateTokenKey64
                .replace("-----BEGIN PRIVATE KEY-----", "")
                .replace("-----END PRIVATE KEY-----", "")
                .replaceAll("\\s", "");
        this.privateTokenKey = Base64.getDecoder().decode(privateTokenKey64);

        String publicTokenKey64 = new String(publicTokenKey, StandardCharsets.UTF_8);;
        publicTokenKey64 = publicTokenKey64
                .replace("-----BEGIN PUBLIC KEY-----", "")
                .replace("-----END PUBLIC KEY-----", "")
                .replaceAll("\\s", "");
        this.publicTokenKey = Base64.getDecoder().decode(publicTokenKey64);
    }

    public List<byte[]> getPlayerCertificateKeys() {
        return playerCertificateKeys;
    }

    public void setPlayerCertificateKeys(List<byte[]> playerCertificateKeys) {
        this.playerCertificateKeys = playerCertificateKeys;
    }

    public String getApiUrl() {
        return apiUrl;
    }

    public long getTokenExpireSec() {
        return tokenExpireSec;
    }

    public byte[] getPrivateTokenKey() {
        return privateTokenKey;
    }

    public byte[] getPublicTokenKey() {
        return publicTokenKey;
    }

    public void setPublicTokenKey(byte[] publicTokenKey) {
        this.publicTokenKey = publicTokenKey;
    }

    public List<byte[]> getProfilePropertyKeys() {
        return profilePropertyKeys;
    }

    public void setProfilePropertyKeys(List<byte[]> profilePropertyKeys) {
        this.profilePropertyKeys = profilePropertyKeys;
    }

    public byte[] getOrCreatePrivateKey() throws Exception {
        File privateKeyFile = new File(PRIVATE_TOKEN_KEY_PATH);

        if (!privateKeyFile.exists()) {
            KeyPairGenerator keyPairGenerator = KeyPairGenerator.getInstance("RSA");
            keyPairGenerator.initialize(2048);
            java.security.KeyPair keyPair = keyPairGenerator.generateKeyPair();
            PrivateKey privateKey = keyPair.getPrivate();

            try (JcaPEMWriter pemWriter = new JcaPEMWriter(new FileWriter(privateKeyFile))) {
                pemWriter.writeObject(new JcaPKCS8Generator(privateKey, null));
            }
            System.out.println("Private key created and saved to rsakey.pem.");
        } else {
            System.out.println("Private key already exists.");
        }

        privateTokenKey = Files.readAllBytes(privateKeyFile.toPath());
        return privateTokenKey;
    }

    public byte[] getOrCreatePublicKey() throws Exception {
        File publicKeyFile = new File(PUBLIC_TOKEN_KEY_PATH);

        if (!publicKeyFile.exists()) {
            String privateKeyContent = new String(getOrCreatePrivateKey(), StandardCharsets.UTF_8);

            PrivateKey privateKey;
            try (PEMParser pemParser = new PEMParser(new StringReader(privateKeyContent))) {
                Object object = pemParser.readObject();
                JcaPEMKeyConverter converter = new JcaPEMKeyConverter();

                if (object instanceof PEMKeyPair) {
                    java.security.KeyPair keyPair = converter.getKeyPair((PEMKeyPair) object);
                    privateKey = keyPair.getPrivate();
                } else if (object instanceof PrivateKeyInfo) {
                    privateKey = converter.getPrivateKey((PrivateKeyInfo) object);
                } else {
                    System.out.println("Invalid private key format.");
                    return null;
                }
            }

            RSAPrivateCrtKey rsaPrivateKey = (RSAPrivateCrtKey) privateKey;
            RSAPublicKeySpec publicKeySpec = new RSAPublicKeySpec(
                    rsaPrivateKey.getModulus(), rsaPrivateKey.getPublicExponent()
            );
            KeyFactory keyFactory = KeyFactory.getInstance("RSA");
            PublicKey publicKey = keyFactory.generatePublic(publicKeySpec);

            try (JcaPEMWriter pemWriter = new JcaPEMWriter(new FileWriter(publicKeyFile))) {
                pemWriter.writeObject(publicKey);
            }
            System.out.println("Public key created and saved to rsapubkey.pem.");
        } else {
            System.out.println("Public key already exists.");
        }

        // Read the public key content from the file
        publicTokenKey = Files.readAllBytes(publicKeyFile.toPath());
        return publicTokenKey;
    }

    private long getEnvAsLong(String envVar, long defaultValue) {
        String value = System.getenv(envVar);
        if (value != null) {
            return Long.parseLong(value);
        } else {
            System.out.println("Env " + envVar + " missed. Will be using default value: " + defaultValue);
        }
        return defaultValue;
    }

    private String getEnvAsString(String envVar, String defaultValue) {
        String value = System.getenv(envVar);
        if (value != null) {
            return value;
        } else {
            System.out.println("Env " + envVar + " missed. Will be using default value: " + defaultValue);
        }
        return defaultValue;
    }
}