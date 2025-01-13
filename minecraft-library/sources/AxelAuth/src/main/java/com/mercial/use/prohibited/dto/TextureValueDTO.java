package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

@Serdeable
@Introspected
public class TextureValueDTO {
    @NotNull
    long timestamp;
    @NotNull
    String profileId;
    @NotNull
    String profileName;
    @NotNull
    TextureMapDTO textures;

    public TextureValueDTO(long timestamp, String profileId, String profileName, TextureMapDTO textures) {
        this.timestamp = timestamp;
        this.profileId = profileId;
        this.profileName = profileName;
        this.textures = textures;
    }

    @NotNull
    public long getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(@NotNull long timestamp) {
        this.timestamp = timestamp;
    }

    public @NotNull String getProfileId() {
        return profileId;
    }

    public void setProfileId(@NotNull String profileId) {
        this.profileId = profileId;
    }

    public @NotNull String getProfileName() {
        return profileName;
    }

    public void setProfileName(@NotNull String profileName) {
        this.profileName = profileName;
    }

    public @NotNull TextureMapDTO getTextures() {
        return textures;
    }

    public void setTextures(@NotNull TextureMapDTO textures) {
        this.textures = textures;
    }
}
