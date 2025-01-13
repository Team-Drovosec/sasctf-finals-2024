package com.mercial.use.prohibited.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

@Serdeable
@Introspected
public class AuthlibInjectorMetaDTO {
    @NotNull
    private String implementationName;
    @NotNull
    private String implementationVersion;
    @NotNull
    private AuthlibInjectorLinksDTO links;
    @NotNull
    private String serverName;
    @JsonProperty("feature.enable_profile_key")
    @NotNull
    private Boolean featureEnableProfileKey;

    public AuthlibInjectorMetaDTO(String implementationName, String implementationVersion, AuthlibInjectorLinksDTO links, String serverName, Boolean featureEnableProfileKey) {
        this.implementationName = implementationName;
        this.implementationVersion = implementationVersion;
        this.links = links;
        this.serverName = serverName;
        this.featureEnableProfileKey = featureEnableProfileKey;
    }

    public @NotNull String getImplementationName() {
        return implementationName;
    }

    public void setImplementationName(@NotNull String implementationName) {
        this.implementationName = implementationName;
    }

    public @NotNull String getImplementationVersion() {
        return implementationVersion;
    }

    public void setImplementationVersion(@NotNull String implementationVersion) {
        this.implementationVersion = implementationVersion;
    }

    public @NotNull AuthlibInjectorLinksDTO getLinks() {
        return links;
    }

    public void setLinks(@NotNull AuthlibInjectorLinksDTO links) {
        this.links = links;
    }

    public @NotNull String getServerName() {
        return serverName;
    }

    public void setServerName(@NotNull String serverName) {
        this.serverName = serverName;
    }

    public @NotNull Boolean getFeatureEnableProfileKey() {
        return featureEnableProfileKey;
    }

    public void setFeatureEnableProfileKey(@NotNull Boolean featureEnableProfileKey) {
        this.featureEnableProfileKey = featureEnableProfileKey;
    }
}
