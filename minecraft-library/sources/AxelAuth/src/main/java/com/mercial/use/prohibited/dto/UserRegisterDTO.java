package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

@Serdeable
@Introspected
public class UserRegisterDTO {
    @NotNull
    @NotBlank
    String username;

    @NotNull
    @NotBlank
    String playerName;

    @NotNull
    @NotBlank
    String password;

    public UserRegisterDTO(String username, String playerName, String password) {
        this.username = username;
        this.playerName = playerName;
        this.password = password;
    }

    public @NotNull @NotBlank String getUsername() {
        return username;
    }

    public void setUsername(@NotNull @NotBlank String username) {
        this.username = username;
    }

    public @NotNull @NotBlank String getPlayerName() {
        return playerName;
    }

    public void setPlayerName(@NotNull @NotBlank String playerName) {
        this.playerName = playerName;
    }

    public @NotNull @NotBlank String getPassword() {
        return password;
    }

    public void setPassword(@NotNull @NotBlank String password) {
        this.password = password;
    }
}
