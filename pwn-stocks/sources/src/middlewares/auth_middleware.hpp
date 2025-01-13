#pragma once

#include "userver/fs/blocking/read.hpp"
#include "userver/fs/blocking/write.hpp"
#include "userver/server/middlewares/configuration.hpp"
#include "userver/server/middlewares/http_middleware_base.hpp"
#include <consts.hpp>
#include <cstdint>
#include <jwt-cpp/jwt.h>
#include <openssl/rand.h>
#include <userver/components/component_list.hpp>
#include <userver/formats/json.hpp>
#include <userver/server/handlers/http_handler_base.hpp>
#include <userver/server/handlers/http_handler_json_base.hpp>

namespace tt { namespace middlewares {

    class AuthMiddleware : public userver::server::middlewares::HttpMiddlewareBase
    {
    public:
        static constexpr std::string_view kName = "auth-middleware";

        explicit AuthMiddleware(const userver::server::handlers::HttpHandlerBase& /*handler*/)
        {}

    private:
        void HandleRequest(userver::server::http::HttpRequest& request,
                           userver::server::request::RequestContext& context) const override;
    };

    class AuthFactory final : public userver::server::middlewares::HttpMiddlewareFactoryBase
    {
    public:
        static constexpr std::string_view kName{ AuthMiddleware::kName };

        AuthFactory(const userver::components::ComponentConfig& config,
                    const userver::components::ComponentContext& context)
            : HttpMiddlewareFactoryBase(config, context)
        {}

        static userver::yaml_config::Schema GetStaticConfigSchema();

    private:
        std::unique_ptr<userver::server::middlewares::HttpMiddlewareBase> Create(
            const userver::server::handlers::HttpHandlerBase& handler,
            userver::yaml_config::YamlConfig /*middleware_config*/) const override;
    };

    class AuthMiddlewarePipelineBuilder final
        : public userver::server::middlewares::HandlerPipelineBuilder
    {
    public:
        using HandlerPipelineBuilder::HandlerPipelineBuilder;

        userver::server::middlewares::MiddlewaresList BuildPipeline(
            userver::server::middlewares::MiddlewaresList server_middleware_pipeline) const override
        {
            auto& pipeline = server_middleware_pipeline;
            pipeline.emplace_back(AuthMiddleware::kName);

            return pipeline;
        }
    };
}}

template<>
inline constexpr bool userver::components::kHasValidate<tt::middlewares::AuthFactory> = true;

template<>
inline constexpr auto userver::components::kConfigFileMode<tt::middlewares::AuthFactory> =
    userver::components::ConfigFileMode::kNotRequired;
