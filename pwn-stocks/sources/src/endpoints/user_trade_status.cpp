#include "user_trade_status.hpp"
#include "boost/uuid/uuid.hpp"
#include "boost/uuid/uuid_io.hpp"
#include "endpoints/stock_price.hpp"
#include "endpoints/user_info.hpp"
#include "rust_ffi.hpp"
#include "sql/queries.hpp"
#include "userver/engine/async.hpp"
#include "userver/engine/sleep.hpp"
#include "userver/logging/log.hpp"
#include "userver/storages/postgres/cluster.hpp"
#include "userver/storages/postgres/io/row_types.hpp"
#include "userver/utils/async.hpp"
#include "utils.hpp"

namespace tt { namespace endpoints {
    TradeStatusResponseBody TradeStatusHandler::TradeStatus(
        TradeStatusRequestBody& request,
        userver::server::request::RequestContext& context) const
    {
        if (!utils::IsValidUuid(request.trade_id)) {
            throw utils::PrepareJsonError("Invalid trade_id");
        }

        storages::postgres::ResultSet res =
            pg_cluster_->Execute(storages::postgres::ClusterHostType::kSlave,
                                 tt::sql::kSelectTradeByIdAndUser,
                                 request.trade_id,
                                 context.GetData<std::string>("username"));
        if (res.IsEmpty()) {
            throw utils::PrepareJsonError("Trade not found");
        }

        auto trade = res.AsSingleRow<UserTrade>(storages::postgres::kRowTag);

        return TradeStatusResponseBody{
            trade.net_profit,
            trade.name,
            trade.description,
            trade.strategy,
            trade.strategy_integrity,
            trade.status,
            std::to_string(trade.timestamp.GetUnderlying().time_since_epoch().count()),
        };
    }
}}
