package com.mercial.use.prohibited.controller;

import com.mercial.use.prohibited.AppConfig;
import com.mercial.use.prohibited.domain.Client;
import com.mercial.use.prohibited.repository.ClientRepository;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;

import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;
import java.security.Key;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.Optional;

public class TokenAuthService {
    private AppConfig config;
    private Key key;
    private final ClientRepository clientRepository;
    private static final Instant DISTANT_FUTURE = Instant.parse("9999-12-31T23:59:59Z");


    public TokenAuthService(AppConfig config, ClientRepository clientRepository) {
        this.config = config;
        this.key = createSecretKey(config.getPrivateTokenKey());
        this.clientRepository = clientRepository;
    }

    private SecretKey createSecretKey(byte[] secretStr) {
        byte[] keyBytes = secretStr;
        return new SecretKeySpec(keyBytes, SignatureAlgorithm.HS512.getJcaName());
    }

    public String makeAccessToken(Client client) throws Exception {
        Instant now = Instant.now();
        Instant expiresAt = config.getTokenExpireSec() > 0
                ? now.plus(config.getTokenExpireSec(), ChronoUnit.SECONDS)
                : DISTANT_FUTURE;

        return Jwts.builder()
                .setSubject(client.getUuid())
                .setIssuedAt(Date.from(now))
                .setExpiration(Date.from(expiresAt))
                .setIssuer("Cocos2d")
                .claim("version", client.getVersion())
                .signWith(key, SignatureAlgorithm.HS512)
                .compact();
    }

    public Client getClient(String accessToken) {
        try {
            Claims claims = Jwts.parser()
                    .setSigningKey(key)
                    .build()
                    .parseClaimsJws(accessToken)
                    .getBody();

            String uuid = claims.getSubject();
            Integer version = claims.get("version", Integer.class);
            Date staleAt = claims.get("exp", Date.class);

            Optional<Client> clientRow = clientRepository.findByUuid(uuid);
            if (clientRow.isEmpty()) {
                return null;
            }
            Client client = clientRow.get();

            if (Instant.now().isAfter(staleAt.toInstant())) {
                return null;
            }

            if (!uuid.equals(client.getUuid()) || !version.equals(client.getVersion())) {
                return null;
            }

            return client;
        } catch (JwtException | IllegalArgumentException e) {
            return null;
        }
    }
}
