package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

import java.util.List;

@Serdeable
@Introspected
public class SessionProfileResponseDTO {
    @NotNull
    String id;
    @NotNull
    String name;
    @NotNull
    List<SessionProfilePropertyDTO> properties;

    public SessionProfileResponseDTO(String id, String name, List<SessionProfilePropertyDTO> properties) {
        this.id = id;
        this.name = name;
        this.properties = properties;
    }

    public @NotNull String getId() {
        return id;
    }

    public void setId(@NotNull String id) {
        this.id = id;
    }

    public @NotNull String getName() {
        return name;
    }

    public void setName(@NotNull String name) {
        this.name = name;
    }

    public @NotNull List<SessionProfilePropertyDTO> getProperties() {
        return properties;
    }

    public void setProperties(@NotNull List<SessionProfilePropertyDTO> properties) {
        this.properties = properties;
    }
}
