package com.mercial.use.prohibited.error;

import com.mercial.use.prohibited.dto.ErrorDTO;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpResponseFactory;
import io.micronaut.http.HttpStatus;

public class AuthError {
    public final static HttpResponse<ErrorDTO> invalidCredentialsBlob = HttpResponseFactory.INSTANCE.status(HttpStatus.UNAUTHORIZED).body(new ErrorDTO(
        null,
        "ForbiddenOperationException",
        "Invalid credentials. Invalid username or password."
    ));

    public final static HttpResponse<ErrorDTO> invalidAccessTokenBlob = HttpResponseFactory.INSTANCE.status(HttpStatus.UNAUTHORIZED).body(new ErrorDTO(
        null,
        "ForbiddenOperationException",
        "Invalid token."
    ));
}
