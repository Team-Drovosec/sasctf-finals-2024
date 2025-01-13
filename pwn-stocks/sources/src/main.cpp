#include <userver/clients/dns/component.hpp>
#include <userver/clients/http/component.hpp>
#include <userver/components/minimal_server_component_list.hpp>
#include <userver/server/handlers/ping.hpp>
#include <userver/server/handlers/tests_control.hpp>
#include <userver/storages/postgres/component.hpp>
#include <userver/testsuite/testsuite_support.hpp>
#include <userver/utils/daemon_run.hpp>

#include "background_task_manager.hpp"
#include "endpoints/stock_price.hpp"
#include "endpoints/trade_history.hpp"
#include "endpoints/user_trade_status.hpp"
#include "endpoints/user_trade_submit.hpp"
#include "userver/components/fs_cache.hpp"

#include "endpoints/login.hpp"
#include "endpoints/register.hpp"
#include "endpoints/user_info.hpp"
#include "jwt_key_generator.hpp"
#include "middlewares/auth_middleware.hpp"

int main(int argc, char* argv[])
{
    // Generate a private key for JWT signing
    tt::JWTKeyGenerator::GetInstance().GenerateOrGetPrivateKey();

    auto component_list = userver::components::MinimalServerComponentList()
                              .Append<userver::server::handlers::Ping>()
                              .Append<userver::components::HttpClient>()
                              .Append<userver::clients::dns::Component>()
                              .Append<userver::components::Postgres>("postgres-db")
                              .Append<userver::components::TestsuiteSupport>()
                              .Append<tt::endpoints::LoginHandler>()
                              .Append<tt::endpoints::RegisterHandler>()
                              .Append<tt::endpoints::UserInfoHandler>()
                              .Append<tt::endpoints::StockPriceHandler>()
                              .Append<tt::endpoints::TradeSubmitHandler>()
                              .Append<tt::endpoints::TradeStatusHandler>()
                              .Append<tt::endpoints::TradeHistoryHandler>()
                              .Append<tt::BackgroundTaskManager>()
                              .Append<tt::middlewares::AuthMiddlewarePipelineBuilder>(
                                  "auth-middleware-pipeline-builder")
                              .Append<tt::middlewares::AuthFactory>();

    return userver::utils::DaemonMain(argc, argv, component_list);
}
