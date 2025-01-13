#include "endpoints/register.hpp"
#include "consts.hpp"
#include "schemas/trusted_trading.hpp"
#include "sql/queries.hpp"
#include "userver/storages/postgres/cluster.hpp"
#include "userver/storages/postgres/io/chrono.hpp"

namespace tt { namespace endpoints {

    void RegisterHandler::CreateUser(const std::string& username, const std::string& password) const
    {
        pg_cluster_->Execute(
            storages::postgres::ClusterHostType::kMaster,
            tt::sql::kInsertUser,
            username,
            password,
            storages::postgres::TimePointWithoutTz{ std::chrono::system_clock::now() });
    }

    RegisterResponseBody RegisterHandler::Register(RegisterRequestBody& request) const
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

        // Check if the user already exists
        storages::postgres::ResultSet res = pg_cluster_->Execute(
            storages::postgres::ClusterHostType::kSlave, tt::sql::kSelectUser, request.username);

        if (!res.IsEmpty()) {
            throw utils::PrepareJsonError("User already exists");
        }

        CreateUser(request.username, request.password);

        return RegisterResponseBody{ fmt::format("User {} registered successfully",
                                                 request.username) };
    }
}}
