#pragma once

#include <userver/storages/postgres/query.hpp>

namespace tt::sql {

    const userver::storages::postgres::Query kSelectUser{
        "SELECT username, password_hash, balance, stocks, timestamp "
        "FROM trusted_trading.users WHERE username=$1",
        userver::storages::postgres::Query::Name{ "select_user" }
    };

    const userver::storages::postgres::Query kSelectUserByPassword{
        "SELECT username, password_hash, balance, stocks, timestamp "
        "FROM trusted_trading.users WHERE username=$1 AND password_hash=encode(digest($2, "
        "'sha256'), "
        "'hex')",
        userver::storages::postgres::Query::Name{ "select_user_by_password_hash" }
    };

    const userver::storages::postgres::Query kInsertUser{
        "INSERT INTO trusted_trading.users (username, password_hash, timestamp) "
        "VALUES ($1, encode(digest($2, 'sha256'), 'hex'), $3)",
        userver::storages::postgres::Query::Name{ "insert_user" }
    };

    const userver::storages::postgres::Query kUpdateUserBalanceAndStocks{
        "UPDATE trusted_trading.users SET balance=$2, stocks=$3 "
        "WHERE username=$1",
        userver::storages::postgres::Query::Name{ "update_user_balance_and_stocks" }
    };

    const userver::storages::postgres::Query kInsertTrade{
        "INSERT INTO trusted_trading.trades (trade_id, username, net_profit, name, description, "
        "strategy, strategy_integrity, status, timestamp) "
        "VALUES (uuid_generate_v4(), $1, $2, $3, $4, $5, $6, $7, NOW())"
        "RETURNING trade_id",
        userver::storages::postgres::Query::Name{ "insert_trade" }
    };

    // Select all trades
    const userver::storages::postgres::Query kSelectTrades{
        "SELECT trade_id, username, net_profit, name, description, strategy, strategy_integrity, "
        "status, timestamp "
        "FROM trusted_trading.trades ORDER BY timestamp DESC",
        userver::storages::postgres::Query::Name{ "select_trades" }
    };

    // Select all trades for a specific user
    const userver::storages::postgres::Query kSelectTradesByUser{
        "SELECT trade_id, username, net_profit, name, description, strategy, strategy_integrity, "
        "status, timestamp "
        "FROM trusted_trading.trades WHERE username=$1 ORDER BY timestamp DESC",
        userver::storages::postgres::Query::Name{ "select_trades_by_user" }
    };

    // Select any `pending` trade for a specific user
    const userver::storages::postgres::Query kSelectPendingTradeByUser{
        "SELECT trade_id, username, net_profit, name, description, strategy, strategy_integrity, "
        "status, timestamp "
        "FROM trusted_trading.trades WHERE username=$1 AND status='pending'",
        userver::storages::postgres::Query::Name{ "select_pending_trade_by_user" }
    };

    // Select a specific trade by trade_id
    const userver::storages::postgres::Query kSelectTradeById{
        "SELECT trade_id, username, net_profit, name, description, strategy, strategy_integrity, "
        "status, timestamp "
        "FROM trusted_trading.trades WHERE trade_id=uuid($1)",
        userver::storages::postgres::Query::Name{ "select_trade_by_id" }
    };

    const userver::storages::postgres::Query kSelectTradeByIdAndUser{
        "SELECT trade_id, username, net_profit, name, description, strategy, strategy_integrity, "
        "status, timestamp "
        "FROM trusted_trading.trades WHERE trade_id=uuid($1) AND username=$2",
        userver::storages::postgres::Query::Name{ "select_trade_by_id_and_user" }
    };

    // Update a trade (if needed)
    const userver::storages::postgres::Query kUpdateTrade{
        "UPDATE trusted_trading.trades SET net_profit=$2, name=$3, description=$4, strategy=$5, "
        "status=$6, "
        "strategy_integrity=$7, timestamp=NOW() "
        "WHERE trade_id=$1",
        userver::storages::postgres::Query::Name{ "update_trade" }
    };

    // Update a trade (if needed)
    const userver::storages::postgres::Query kUpdateTradeProfitStatus{
        "UPDATE trusted_trading.trades SET net_profit=$2, status=$3"
        "WHERE trade_id=$1",
        userver::storages::postgres::Query::Name{ "update_trade_profit_status" }
    };

    // Delete a trade (if needed)
    const userver::storages::postgres::Query kDeleteTrade{
        "DELETE FROM trusted_trading.trades WHERE trade_id=$1",
        userver::storages::postgres::Query::Name{ "delete_trade" }
    };
}
