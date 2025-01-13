package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

@Serdeable
@Introspected
public class SessionProfilePropertyDTO {
    @NotNull
    String name;
    @NotNull
    String value;
    String signature;

    public SessionProfilePropertyDTO(String name, String value, String signature) {
        this.name = name;
        this.value = value;
        this.signature = signature;
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

    public String getSignature() {
        return signature;
    }

    public void setSignature(String signature) {
        this.signature = signature;
    }
}
