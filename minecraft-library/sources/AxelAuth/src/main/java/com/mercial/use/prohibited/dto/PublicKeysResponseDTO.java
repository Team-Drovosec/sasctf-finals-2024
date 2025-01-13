package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

import java.util.List;

@Serdeable
@Introspected
public class PublicKeysResponseDTO {
    @NotNull
    List<SerializedKeyDTO> playerCertificateKeys;
    @NotNull
    List<SerializedKeyDTO> profilePropertyKeys;

    public PublicKeysResponseDTO(List<SerializedKeyDTO> playerCertificateKeys, List<SerializedKeyDTO> profilePropertyKeys) {
        this.playerCertificateKeys = playerCertificateKeys;
        this.profilePropertyKeys = profilePropertyKeys;
    }

    public @NotNull List<SerializedKeyDTO> getPlayerCertificateKeys() {
        return playerCertificateKeys;
    }

    public void setPlayerCertificateKeys(@NotNull List<SerializedKeyDTO> playerCertificateKeys) {
        this.playerCertificateKeys = playerCertificateKeys;
    }

    public @NotNull List<SerializedKeyDTO> getProfilePropertyKeys() {
        return profilePropertyKeys;
    }

    public void setProfilePropertyKeys(@NotNull List<SerializedKeyDTO> profilePropertyKeys) {
        this.profilePropertyKeys = profilePropertyKeys;
    }
}
