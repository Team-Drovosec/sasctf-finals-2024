package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

@Serdeable
@Introspected
public class UserPropertyDTO {
    @NotNull
    private String name;
    @NotNull
    private String value;

    public UserPropertyDTO(String name, String value) {
        this.name = name;
        this.value = value;
    }

    public @NotNull String getName() {
        return name;
    }

    public void setName(@NotNull String name) {
        this.name = name;
    }

    public @NotNull String getValue() {
        return value;
    }

    public void setValue(@NotNull String value) {
        this.value = value;
    }
}
