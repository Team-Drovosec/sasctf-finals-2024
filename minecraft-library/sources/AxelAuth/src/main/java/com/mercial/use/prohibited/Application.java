package com.mercial.use.prohibited;

import com.mercial.use.prohibited.domain.Client;
import com.mercial.use.prohibited.domain.User;
import io.micronaut.core.annotation.Introspected;
import io.micronaut.runtime.Micronaut;
import io.micronaut.serde.annotation.SerdeImport;
import jakarta.persistence.Entity;


@Introspected(packages = "com.mercial.use.prohibited.domain", includedAnnotations = Entity.class)
@SerdeImport(User.class)
@SerdeImport(Client.class)
public class Application {

    public static void main(String[] args) {
        Micronaut.run(Application.class, args);
    }
}