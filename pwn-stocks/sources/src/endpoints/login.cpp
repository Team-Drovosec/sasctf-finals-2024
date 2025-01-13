#include "endpoints/login.hpp"

#include "jwt_key_generator.hpp"
#include "sql/queries.hpp"
#include "userver/storages/postgres/cluster.hpp"
#include "userver/storages/postgres/result_set.hpp"
#include "utils.hpp"
#include <chrono>
#include <jwt-cpp/jwt.h>

namespace tt { namespace endpoints {

    bool LoginHandler::ValidateCredentials(const std::string& username,
                                           const std::string& password) const
    {
        storages::postgres::ResultSet res =
            pg_cluster_->Execute(storages::postgres::ClusterHostType::kSlave,
                                 tt::sql::kSelectUserByPassword,
                                 username,
                                 password);

        return !res.IsEmpty();
    }

    std::string LoginHandler::GenerateToken(const std::string& username)
    {
        const std::chrono::minutes kTokenLifetime{ 15 };

        auto token = jwt::create()
                         .set_issuer(tt::JWTKeyGenerator::issuer)
                         .set_type("JWS")
                         .set_subject(username)
                         .set_audience("user")
                         .set_issued_at(std::chrono::system_clock::now())
                         .set_expires_at(std::chrono::system_clock::now() + kTokenLifetime)
                         .sign(jwt::algorithm::hs256{
                             JWTKeyGenerator::GetInstance().GenerateOrGetPrivateKey() });
        return token;
    }

    LoginResponseBody LoginHandler::Login(LoginRequestBody& request) const
    {
        if (request.username.empty()) {
            throw utils::PrepareJsonError("Username is empty");
        }

        if (request.password.empty()) {
            throw utils::PrepareJsonError("Password is empty");
        }

        if (request.password.size() < consts::kMinPasswordLength) {
            throw utils::PrepareJsonError("Password is too short");
        }

        if (request.password.size() > consts::kMaxPasswordLength) {
            throw utils::PrepareJsonError("Password is too long");
        }

        if (request.username.size() > consts::kMaxUsernameLength) {
            throw utils::PrepareJsonError("Username is too long");
        }

        if (ValidateCredentials(request.username, request.password)) {
            auto token = GenerateToken(request.username);
            return LoginResponseBody{ token };
        }

        throw utils::PrepareJsonError("Invalid username or password");
    }

}}