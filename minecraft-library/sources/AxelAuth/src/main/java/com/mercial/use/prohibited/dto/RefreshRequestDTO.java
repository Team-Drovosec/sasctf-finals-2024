package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

@Serdeable
@Introspected
public class RefreshRequestDTO {
    @NotNull
    private String accessToken;
    @NotNull
    private String clientToken;
    @NotNull
    private Boolean requestUser;

    public RefreshRequestDTO(String accessToken, String clientToken, Boolean requestUser) {
        this.accessToken = accessToken;
        this.clientToken = clientToken;
        this.requestUser = requestUser;
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

    public @NotNull Boolean getRequestUser() {
        return requestUser;
    }

    public void setRequestUser(@NotNull Boolean requestUser) {
        this.requestUser = requestUser;
    }
}
