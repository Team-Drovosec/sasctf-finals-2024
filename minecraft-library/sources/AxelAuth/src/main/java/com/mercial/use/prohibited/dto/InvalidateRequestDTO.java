package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

@Serdeable
@Introspected
public class InvalidateRequestDTO {
    @NotNull
    private String accessToken;
    @NotNull
    private String clientToken;

    public InvalidateRequestDTO(String accessToken, String clientToken) {
        this.accessToken = accessToken;
        this.clientToken = clientToken;
    }

    public @NotNull String getAccessToken() {
        return accessToken;
    }

    public void setAccessToken(@NotNull String accessToken) {
        this.accessToken = accessToken;
    }

    public @NotNull String getClientToken() {
        return clientToken;
    }

    public void setClientToken(@NotNull String clientToken) {
        this.clientToken = clientToken;
    }
}
