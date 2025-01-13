package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

@Serdeable
@Introspected
public class SerializedKeyDTO {
    @NotNull
    private String publicKey;

    public SerializedKeyDTO(String publicKey) {
        this.publicKey = publicKey;
    }

    public @NotNull String getPublicKey() {
        return publicKey;
    }

    public void setPublicKey(@NotNull String publicKey) {
        this.publicKey = publicKey;
    }
}
