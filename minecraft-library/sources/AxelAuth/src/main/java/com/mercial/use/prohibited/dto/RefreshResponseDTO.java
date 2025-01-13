package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

import java.util.List;

@Serdeable
@Introspected
public class RefreshResponseDTO {
    @NotNull
    private String accessToken;
    @NotNull
    private String clientToken;
    @NotNull
    private ProfileDTO selectedProfile;
    @NotNull
    private List<ProfileDTO> availableProfiles;
    private UserResponseDTO userResponse;

    public RefreshResponseDTO(String accessToken, String clientToken, ProfileDTO selectedProfile, List<ProfileDTO> availableProfiles, UserResponseDTO userResponse) {
        this.accessToken = accessToken;
        this.clientToken = clientToken;
        this.selectedProfile = selectedProfile;
        this.availableProfiles = availableProfiles;
        this.userResponse = userResponse;
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

    public @NotNull ProfileDTO getSelectedProfile() {
        return selectedProfile;
    }

    public void setSelectedProfile(@NotNull ProfileDTO selectedProfile) {
        this.selectedProfile = selectedProfile;
    }

    public @NotNull List<ProfileDTO> getAvailableProfiles() {
        return availableProfiles;
    }

    public void setAvailableProfiles(@NotNull List<ProfileDTO> availableProfiles) {
        this.availableProfiles = availableProfiles;
    }

    public UserResponseDTO getUserResponse() {
        return userResponse;
    }

    public void setUserResponse(UserResponseDTO userResponse) {
        this.userResponse = userResponse;
    }
}
