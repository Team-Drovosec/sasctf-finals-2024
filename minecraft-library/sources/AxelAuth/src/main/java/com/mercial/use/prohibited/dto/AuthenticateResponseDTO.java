package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

import java.util.List;

@Serdeable
@Introspected
public class AuthenticateResponseDTO {
    @NotNull
    private String accessToken;
    @NotNull
    private String clientToken;
    private ProfileDTO selectedProfile;
    private List<ProfileDTO> availableProfiles;
    private UserResponseDTO user;

    public AuthenticateResponseDTO(String accessToken, String clientToken, ProfileDTO selectedProfile, List<ProfileDTO> availableProfiles, UserResponseDTO user) {
        this.accessToken = accessToken;
        this.clientToken = clientToken;
        this.selectedProfile = selectedProfile;
        this.availableProfiles = availableProfiles;
        this.user = user;
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

    public ProfileDTO getSelectedProfile() {
        return selectedProfile;
    }

    public void setSelectedProfile(ProfileDTO selectedProfile) {
        this.selectedProfile = selectedProfile;
    }

    public List<ProfileDTO> getAvailableProfiles() {
        return availableProfiles;
    }

    public void setAvailableProfiles(List<ProfileDTO> availableProfiles) {
        this.availableProfiles = availableProfiles;
    }

    public UserResponseDTO getUser() {
        return user;
    }

    public void setUser(UserResponseDTO user) {
        this.user = user;
    }
}
