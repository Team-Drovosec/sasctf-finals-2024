#pragma once

#include <userver/components/minimal_server_component_list.hpp>
#include <userver/formats/json.hpp>
#include <userver/formats/json/value.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/handlers/http_handler_base.hpp>
#include <userver/server/handlers/http_handler_json_base.hpp>
#include <userver/server/handlers/json_error_builder.hpp>
#include <userver/server/handlers/legacy_json_error_builder.hpp>

#include "userver/components/component_context.hpp"
#include "userver/components/fs_cache.hpp"
#include "userver/dynamic_config/storage/component.hpp"
#include "userver/fs/fs_cache_client.hpp"
#include "userver/logging/log.hpp"
#include "userver/server/handlers/exceptions.hpp"
#include "userver/server/handlers/http_handler_json_base.hpp"
#include "userver/storages/postgres/component.hpp"
#include "userver/storages/postgres/postgres_fwd.hpp"
#include "userver/yaml_config/merge_schemas.hpp"

#include "schemas/trusted_trading.hpp"
#include "utils.hpp"
#include <string>

namespace tt { namespace endpoints {
    using namespace userver::formats;
    using namespace userver;

    class LoginHandler : public server::handlers::HttpHandlerJsonBase
    {
    public:
        static constexpr std::string_view kName = "handler-login";

        LoginHandler(const components::ComponentConfig& config,
                     const components::ComponentContext& context)
            : HttpHandlerJsonBase(config, context)
            , pg_cluster_(context.FindComponent<components::Postgres>("postgres-db").GetCluster())
        {}

        json::Value HandleRequestJsonThrow(
            const server::http::HttpRequest& /*request*/,
            const json::Value& json,
            server::request::RequestContext& /*context*/) const override
        {
            try {
                auto request_dom = json.As<LoginRequestBody>();
                auto response_dom = Login(request_dom);
                auto response_json = json::ValueBuilder{ response_dom }.ExtractValue();
                return response_json;
            } catch (const json::ExceptionWithPath& ex) {
                throw utils::PrepareJsonError(ex.GetMessage());
            }
        }

    private:
        bool ValidateCredentials(const std::string& username, const std::string& password) const;
        static std::string GenerateToken(const std::string& username);
        LoginResponseBody Login(LoginRequestBody& request) const;

        storages::postgres::ClusterPtr pg_cluster_;
    };
}}