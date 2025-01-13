package com.mercial.use.prohibited.dto;

import java.util.Date;

class TokenDTO {
    private String subject;
    private Date issuedAt;
    private Date expiration;
    private String issuer;
    private String version;
    private Date staleAt;

    public TokenDTO(String subject, Date issuedAt, Date expiration, String issuer, String version, Date staleAt) {
        this.subject = subject;
        this.issuedAt = issuedAt;
        this.expiration = expiration;
        this.issuer = issuer;
        this.version = version;
        this.staleAt = staleAt;
    }

    public String getSubject() {
        return subject;
    }

    public void setSubject(String subject) {
        this.subject = subject;
    }

    public Date getIssuedAt() {
        return issuedAt;
    }

    public void setIssuedAt(Date issuedAt) {
        this.issuedAt = issuedAt;
    }

    public Date getExpiration() {
        return expiration;
    }

    public void setExpiration(Date expiration) {
        this.expiration = expiration;
    }

    public String getIssuer() {
        return issuer;
    }

    public void setIssuer(String issuer) {
        this.issuer = issuer;
    }

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public Date getStaleAt() {
        return staleAt;
    }

    public void setStaleAt(Date staleAt) {
        this.staleAt = staleAt;
    }
}
