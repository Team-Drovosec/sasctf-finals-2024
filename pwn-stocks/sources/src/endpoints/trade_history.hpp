#pragma once

#include <userver/components/minimal_server_component_list.hpp>
#include <userver/formats/json.hpp>
#include <userver/formats/json/value.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/handlers/http_handler_base.hpp>
#include <userver/server/handlers/http_handler_json_base.hpp>
#include <userver/server/handlers/json_error_builder.hpp>
#include <userver/server/handlers/legacy_json_error_builder.hpp>

#include "background_task_manager.hpp"
#include "userver/components/component_context.hpp"
#include "userver/components/fs_cache.hpp"
#include "userver/concurrent/background_task_storage.hpp"
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

    class TradeHistoryHandler final : public server::handlers::HttpHandlerJsonBase
    {
    public:
        static constexpr std::string_view kName = "handler-trade-history";

        TradeHistoryHandler(const components::ComponentConfig& config,
                            const components::ComponentContext& context)
            : HttpHandlerJsonBase(config, context)
            , pg_cluster_(context.FindComponent<components::Postgres>("postgres-db").GetCluster())
            , background_task_manager_(context.FindComponent<BackgroundTaskManager>())
        {}

        json::Value HandleRequestJsonThrow(
            const userver::server::http::HttpRequest& /*request*/,
            const json::Value& json,
            userver::server::request::RequestContext& context) const override
        {
            try {
                auto request_dom = json.As<TradeHistoryRequestBody>();
                auto response_dom = TradeHistory(request_dom, context);
                auto response_json = json::ValueBuilder{ response_dom }.ExtractValue();
                return response_json;
            } catch (const userver::formats::json::ExceptionWithPath& ex) {
                throw utils::PrepareJsonError(ex.GetMessage());
            }
        }

    private:
        storages::postgres::ClusterPtr pg_cluster_;
        BackgroundTaskManager& background_task_manager_;

        TradeHistoryResponseBody TradeHistory(
            TradeHistoryRequestBody& request,
            userver::server::request::RequestContext& context) const;
    };
}}