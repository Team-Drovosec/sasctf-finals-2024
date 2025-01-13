package com.mercial.use.prohibited.dto;

import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import jakarta.validation.constraints.NotNull;

import java.util.List;

@Serdeable
@Introspected
public class AuthlibInjectorResponseDTO {
    @NotNull
    private AuthlibInjectorMetaDTO meta;
    @NotNull
    private String signaturePublickey;
    @NotNull
    private List<String> signaturePublickeys;
    @NotNull
    private List<String> skinDomains;

    public AuthlibInjectorResponseDTO(AuthlibInjectorMetaDTO meta, String signaturePublickey, List<String> signaturePublickeys, List<String> skinDomains) {
        this.meta = meta;
        this.signaturePublickey = signaturePublickey;
        this.signaturePublickeys = signaturePublickeys;
        this.skinDomains = skinDomains;
    }

    public @NotNull AuthlibInjectorMetaDTO getMeta() {
        return meta;
    }

    public void setMeta(@NotNull AuthlibInjectorMetaDTO meta) {
        this.meta = meta;
    }

    public @NotNull String getSignaturePublickey() {
        return signaturePublickey;
    }

    public void setSignaturePublickey(@NotNull String signaturePublickey) {
        this.signaturePublickey = signaturePublickey;
    }

    public @NotNull List<String> getSignaturePublickeys() {
        return signaturePublickeys;
    }

    public void setSignaturePublickeys(@NotNull List<String> signaturePublickeys) {
        this.signaturePublickeys = signaturePublickeys;
    }

    public @NotNull List<String> getSkinDomains() {
        return skinDomains;
    }

    public void setSkinDomains(@NotNull List<String> skinDomains) {
        this.skinDomains = skinDomains;
    }
}
