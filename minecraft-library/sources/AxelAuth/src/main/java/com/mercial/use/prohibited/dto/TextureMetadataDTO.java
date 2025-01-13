package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

@Serdeable
@Introspected
public class TextureMetadataDTO {
    @NotNull
    String model;

    public TextureMetadataDTO(String model) {
        this.model = model;
    }

    public @NotNull String getModel() {
        return model;
    }

    public void setModel(@NotNull String model) {
        this.model = model;
    }
}
