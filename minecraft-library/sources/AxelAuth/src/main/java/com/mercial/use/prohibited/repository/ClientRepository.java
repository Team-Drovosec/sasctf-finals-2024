package com.mercial.use.prohibited.repository;

import com.mercial.use.prohibited.domain.Client;
import com.mercial.use.prohibited.domain.User;
import io.micronaut.data.annotation.Repository;
import io.micronaut.data.repository.CrudRepository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ClientRepository extends CrudRepository<Client, String> {
    List<Client> findByUser(User user);

    List<Client> findByUserUuid(String userUuid);

    Optional<Client> findByClientToken(String clientToken);
    Optional<Client> findByUuid(String uuid);

    boolean existsByClientToken(String clientToken);
}