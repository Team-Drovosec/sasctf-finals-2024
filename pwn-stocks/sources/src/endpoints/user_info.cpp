#include "endpoints/user_info.hpp"
#include "boost/uuid/uuid.hpp"
#include "boost/uuid/uuid_io.hpp"
#include "schemas/trusted_trading.hpp"
#include "sql/queries.hpp"
#include "userver/storages/postgres/cluster.hpp"
#include "userver/storages/postgres/io/row_types.hpp"

namespace tt { namespace endpoints {
    UserInfoResponseBody UserInfoHandler::UserInfo(UserInfoRequestBody& /* request */,
                                                   server::request::RequestContext& context) const
    {
        storages::postgres::ResultSet res =
            pg_cluster_->Execute(storages::postgres::ClusterHostType::kSlave,
                                 tt::sql::kSelectUser,
                                 context.GetData<std::string>("username"));

        auto user_db_info = res.AsSingleRow<UserDbInfo>(storages::postgres::kRowTag);

        // Get all the user's trades
        res = pg_cluster_->Execute(storages::postgres::ClusterHostType::kSlave,
                                   tt::sql::kSelectTradesByUser,
                                   user_db_info.username);
        auto trades = res.AsSetOf<UserTrade>(storages::postgres::kRowTag);
        std::vector<std::string> trade_uuids;
        std::transform(
            trades.begin(),
            trades.end(),
            std::back_inserter(trade_uuids),
            [](const UserTrade& trade) { return boost::uuids::to_string(trade.trade_id); });

        return UserInfoResponseBody{ static_cast<int32_t>(user_db_info.stocks),
                                     static_cast<int32_t>(user_db_info.balance),
                                     trade_uuids };
    }
}}
