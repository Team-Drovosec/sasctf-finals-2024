package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

@Serdeable
@Introspected
public class AuthenticateRequestDTO {
    private AgentDTO agent;
    private String clientToken;
    private Boolean requestUser;
    @NotNull
    private String username;
    @NotNull
    private String password;

    public AuthenticateRequestDTO(AgentDTO agent, String clientToken, Boolean requestUser, String username, String password) {
        this.agent = agent;
        this.clientToken = clientToken;
        this.requestUser = requestUser != null ? requestUser : false;
        this.username = username;
        this.password = password;
    }

    public AgentDTO getAgent() {
        return agent;
    }

    public void setAgent(AgentDTO agent) {
        this.agent = agent;
    }

    public String getClientToken() {
        return clientToken;
    }

    public void setClientToken(String clientToken) {
        this.clientToken = clientToken;
    }

    public Boolean getRequestUser() {
        return requestUser;
    }

    public void setRequestUser(Boolean requestUser) {
        this.requestUser = requestUser;
    }

    public @NotNull String getUsername() {
        return username;
    }

    public void setUsername(@NotNull String username) {
        this.username = username;
    }

    public @NotNull String getPassword() {
        return password;
    }

    public void setPassword(@NotNull String password) {
        this.password = password;
    }
}
