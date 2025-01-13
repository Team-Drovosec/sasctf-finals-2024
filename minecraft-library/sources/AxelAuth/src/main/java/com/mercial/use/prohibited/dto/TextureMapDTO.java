package com.mercial.use.prohibited.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;

@JsonInclude(JsonInclude.Include.NON_NULL)
@Serdeable
@Introspected
public class TextureMapDTO {
    @JsonProperty("SKIN")
    TextureDTO skin;
    @JsonProperty("CAPE")
    TextureDTO cape;

    public TextureMapDTO() {}

    public TextureMapDTO(TextureDTO SKIN, TextureDTO CAPE) {
        this.skin = SKIN;
        this.cape = CAPE;
    }

    public TextureDTO getSkin() {
        return skin;
    }

    public void setSkin(TextureDTO skin) {
        this.skin = skin;
    }

    public TextureDTO getCape() {
        return cape;
    }

    public void setCape(TextureDTO cape) {
        this.cape = cape;
    }
}
