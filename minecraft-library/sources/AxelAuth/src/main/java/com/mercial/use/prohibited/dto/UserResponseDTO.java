package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

import java.util.List;

@Serdeable
@Introspected
public class UserResponseDTO {
    @NotNull
    private String id;
    @NotNull
    private List<UserPropertyDTO> properties;

    public UserResponseDTO(String id, List<UserPropertyDTO> properties) {
        this.id = id;
        this.properties = properties;
    }

    public @NotNull String getId() {
        return id;
    }

    public void setId(@NotNull String id) {
        this.id = id;
    }

    public @NotNull List<UserPropertyDTO> getProperties() {
        return properties;
    }

    public void setProperties(@NotNull List<UserPropertyDTO> properties) {
        this.properties = properties;
    }
}
