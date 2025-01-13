#include "middlewares/auth_middleware.hpp"
#include "jwt_key_generator.hpp"
#include "userver/formats/yaml/serialize.hpp"
#include "userver/fs/blocking/read.hpp"
#include "userver/fs/blocking/write.hpp"
#include "userver/server/middlewares/http_middleware_base.hpp"
#include "userver/yaml_config/merge_schemas.hpp"
#include "utils.hpp"
#include <consts.hpp>
#include <cstdint>
#include <jwt-cpp/jwt.h>
#include <openssl/rand.h>
#include <userver/components/component_list.hpp>
#include <userver/formats/json.hpp>
#include <userver/server/handlers/http_handler_base.hpp>
#include <userver/server/handlers/http_handler_json_base.hpp>

namespace tt { namespace middlewares {
    void AuthMiddleware::HandleRequest(userver::server::http::HttpRequest& request,
                                       userver::server::request::RequestContext& context) const
    {
        // Make sure the response is JSON
        request.GetHttpResponse().SetContentType(userver::http::content_type::kApplicationJson);

        constexpr std::string_view kBearer = "Bearer ";

        auto auth_header = request.GetHeader("Authorization");
        if (auth_header.empty() || auth_header.substr(0, kBearer.length()) != kBearer) {
            request.SetResponseStatus(userver::server::http::HttpStatus::kUnauthorized);
            throw utils::PrepareJsonError("Authorization header is missing or invalid");
        }

        auto token = auth_header.substr(kBearer.length());
        try {
            auto decoded = jwt::decode(token);
            auto verifier = jwt::verify()
                                .allow_algorithm(jwt::algorithm::hs256{
                                    JWTKeyGenerator::GetInstance().GenerateOrGetPrivateKey() })
                                .with_issuer(JWTKeyGenerator::issuer);

            verifier.verify(decoded);
            context.SetData("username", decoded.get_subject());
        } catch (const std::exception& e) {
            request.SetResponseStatus(userver::server::http::HttpStatus::kUnauthorized);
            throw utils::PrepareJsonError("Invalid token");
        }

        // Token is valid, proceed to the next handler
        Next(request, context);
    }

    userver::yaml_config::Schema AuthFactory::GetStaticConfigSchema()
    {
        return userver::formats::yaml::FromString(R"(
type: object
description: |
    Middleware for authenticating requests using JWT tokens.
additionalProperties: false
properties: {}
)")
            .As<userver::yaml_config::Schema>();
    }

    std::unique_ptr<userver::server::middlewares::HttpMiddlewareBase> AuthFactory::Create(
        const userver::server::handlers::HttpHandlerBase& handler,
        userver::yaml_config::YamlConfig /*middleware_config*/) const
    {
        return std::make_unique<AuthMiddleware>(handler);
    }
}}