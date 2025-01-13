package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

@Serdeable
@Introspected
public class SessionJoinRequestDTO {
    @NotNull
    private String accessToken;
    @NotNull
    private String selectedProfile;
    @NotNull
    private String serverId;

    public SessionJoinRequestDTO(String accessToken, String selectedProfile, String serverId) {
        this.accessToken = accessToken;
        this.selectedProfile = selectedProfile;
        this.serverId = serverId;
    }

    public @NotNull String getAccessToken() {
        return accessToken;
    }

    public void setAccessToken(@NotNull String accessToken) {
        this.accessToken = accessToken;
    }

    public @NotNull String getSelectedProfile() {
        return selectedProfile;
    }

    public void setSelectedProfile(@NotNull String selectedProfile) {
        this.selectedProfile = selectedProfile;
    }

    public @NotNull String getServerId() {
        return serverId;
    }

    public void setServerId(@NotNull String serverId) {
        this.serverId = serverId;
    }
}
