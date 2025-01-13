package com.mercial.use.prohibited.repository;

import com.mercial.use.prohibited.domain.User;
import io.micronaut.data.annotation.Repository;
import io.micronaut.data.repository.CrudRepository;

import java.util.Optional;

@Repository
public interface UserRepository extends CrudRepository<User, String> {
    Optional<User> findByUsername(String username);

    Optional<User> findByPlayerName(String playerName);

    boolean existsByUsername(String username);

    boolean existsByPlayerName(String playerName);
}