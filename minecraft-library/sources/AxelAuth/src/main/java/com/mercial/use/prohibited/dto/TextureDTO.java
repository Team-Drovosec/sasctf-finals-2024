package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

@Serdeable
@Introspected
public class TextureDTO {
    TextureMetadataDTO metadata;
    @NotNull
    String url;

    public TextureDTO(TextureMetadataDTO metadata, String url) {
        this.metadata = metadata;
        this.url = url;
    }

    public TextureMetadataDTO getMetadata() {
        return metadata;
    }

    public void setMetadata(TextureMetadataDTO metadata) {
        this.metadata = metadata;
    }

    public @NotNull String getUrl() {
        return url;
    }

    public void setUrl(@NotNull String url) {
        this.url = url;
    }
}
