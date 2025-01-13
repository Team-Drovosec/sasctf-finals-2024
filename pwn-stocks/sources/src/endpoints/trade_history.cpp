#include "trade_history.hpp"
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
    TradeHistoryResponseBody TradeHistoryHandler::TradeHistory(
        TradeHistoryRequestBody& request,
        userver::server::request::RequestContext& context) const
    {
        TradeHistoryResponseBody response;

        storages::postgres::ResultSet res = pg_cluster_->Execute(
            storages::postgres::ClusterHostType::kSlave, tt::sql::kSelectTrades);
        auto trades = res.AsSetOf<UserTrade>(storages::postgres::kRowTag);

        response.trades.reserve(trades.Size());
        uint32_t limit = std::min(static_cast<uint64_t>(request.limit.value_or(trades.Size())),
                                  static_cast<uint64_t>(trades.Size()));

        std::transform(
            trades.begin(),
            trades.begin() + limit,
            std::back_inserter(response.trades),
            [](const UserTrade& trade) {
                return TradeHistoryResponseBody::TradesA{
                    boost::uuids::to_string(trade.trade_id),
                    trade.net_profit,
                    trade.strategy_integrity,
                    trade.status,
                    std::to_string(trade.timestamp.GetUnderlying().time_since_epoch().count())
                };
            });

        return response;
    }
}}
