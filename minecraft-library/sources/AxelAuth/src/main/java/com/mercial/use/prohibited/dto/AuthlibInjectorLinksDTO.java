package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

@Serdeable
@Introspected
public class AuthlibInjectorLinksDTO {
    @NotNull
    private String homepage;
    @NotNull
    private String register;

    public AuthlibInjectorLinksDTO(String homepage, String register) {
        this.homepage = homepage;
        this.register = register;
    }

    public @NotNull String getHomepage() {
        return homepage;
    }

    public void setHomepage(@NotNull String homepage) {
        this.homepage = homepage;
    }

    public @NotNull String getRegister() {
        return register;
    }

    public void setRegister(@NotNull String register) {
        this.register = register;
    }
}
