#include "user_trade_submit.hpp"
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

namespace tt { namespace endpoints {

    void TradeSubmitHandler::UpdateUserBalanceAndStocks(const std::string& username,
                                                        const int64_t balance,
                                                        const int64_t stocks) const
    {
        pg_cluster_->Execute(storages::postgres::ClusterHostType::kMaster,
                             tt::sql::kUpdateUserBalanceAndStocks,
                             username,
                             balance,
                             stocks);
    }

    void TradeSubmitHandler::UpdateTradeByUUID(const boost::uuids::uuid trade_id,
                                               const int64_t net_profit,
                                               const std::string& status) const
    {
        pg_cluster_->Execute(storages::postgres::ClusterHostType::kMaster,
                             tt::sql::kUpdateTradeProfitStatus,
                             trade_id,
                             net_profit,
                             status);
    }

    boost::uuids::uuid TradeSubmitHandler::InsertTradeForUser(const std::string& username,
                                                              const std::string& strategy_name,
                                                              const std::string& description,
                                                              const std::string& strategy,
                                                              const std::string& strategy_integrity,
                                                              const std::string& status) const
    {
        storages::postgres::ResultSet res =
            pg_cluster_->Execute(storages::postgres::ClusterHostType::kMaster,
                                 tt::sql::kInsertTrade,
                                 username,
                                 0,
                                 strategy_name,
                                 description,
                                 strategy,
                                 strategy_integrity,
                                 status);

        struct UserTrade
        {
            boost::uuids::uuid trade_id;
        };

        return res.AsSingleRow<UserTrade>(storages::postgres::kRowTag).trade_id;
    }

    TradeSubmitResponseBody TradeSubmitHandler::TradeSubmit(
        TradeSubmitRequestBody& request,
        userver::server::request::RequestContext& context) const
    {
        // Check if the user has any running trades
        storages::postgres::ResultSet res =
            pg_cluster_->Execute(storages::postgres::ClusterHostType::kSlave,
                                 tt::sql::kSelectPendingTradeByUser,
                                 context.GetData<std::string>("username"));
        if (!res.IsEmpty()) {
            throw utils::PrepareJsonError("You already have a pending trade!");
        }

        if (request.name.empty()) {
            throw utils::PrepareJsonError("Trade name is empty");
        }

        if (request.name.size() > 255) {
            throw utils::PrepareJsonError("Trade name is too long");
        }

        if (request.description.empty()) {
            throw utils::PrepareJsonError("Trade description is empty");
        }

        if (request.description.size() > 255) {
            throw utils::PrepareJsonError("Trade description is too long");
        }

        if (request.strategy.empty()) {
            throw utils::PrepareJsonError("Trade strategy is empty");
        }

        constexpr uint32_t kErrorSize = 1024;
        std::string error;
        error.resize(kErrorSize);

        constexpr uint32_t kCodeIntegritySize = 1024;
        std::string code_integrity;
        code_integrity.resize(kCodeIntegritySize);

        void* exe = ffi::compile_expression(request.strategy.c_str(),
                                            code_integrity.data(),
                                            code_integrity.size(),
                                            error.data(),
                                            error.size());

        error.erase(std::find(error.begin(), error.end(), '\0'), error.end());
        error.shrink_to_fit();

        if (exe == nullptr || error[0]) {
            throw utils::PrepareJsonError(fmt::format("Failed to compile strategy: {}", error));
        }

        code_integrity.erase(std::find(code_integrity.begin(), code_integrity.end(), '\0'),
                             code_integrity.end());
        code_integrity.shrink_to_fit();

        if (code_integrity.empty()) {
            throw utils::PrepareJsonError("Empty code integrity");
        }

        auto trade_id =
            InsertTradeForUser(context.GetData<std::string>("username"),
                               request.name,
                               request.description,
                               request.strategy,
                               code_integrity,
                               kTradeStatusStr[static_cast<uint32_t>(TradeStatus::kPending)]);

        res = pg_cluster_->Execute(storages::postgres::ClusterHostType::kSlave,
                                   tt::sql::kSelectUser,
                                   context.GetData<std::string>("username"));
        UserDbInfo user_db_info = res.AsSingleRow<UserDbInfo>(storages::postgres::kRowTag);

        background_task_manager_.AddTask(
            "trade_processor", [this, trade_id, exe, user_db_info]() mutable {
                LOG_INFO() << fmt::format("Processing trade {}", boost::uuids::to_string(trade_id));

                std::string error;
                error.resize(kErrorSize);

                // Wait for ~10 seconds to get the stock prices
                const auto wait_time = std::chrono::seconds{ 12 };
                engine::InterruptibleSleepFor(wait_time);

                // Get the stock prices
                auto stock_prices = g_stock_price_generator_->GetStockPrices();

                // Run the strategy on the last 10 stock prices
                std::string trade_status =
                    kTradeStatusStr[static_cast<uint32_t>(TradeStatus::kCompleted)];
                const uint32_t kStocksToProcess = 10;
                int64_t net_profit = 0;
                for (size_t i = stock_prices.size() - kStocksToProcess; i < stock_prices.size();
                     ++i) {
                    const std::array<char const*, 4> variables = {
                        "BALANCE", "STOCK_PRICE", "HOLDINGS", "HOLDINGS_VALUE"
                    };
                    const std::array<int64_t, 4> values = { user_db_info.balance,
                                                            stock_prices[i - 1].close,
                                                            user_db_info.stocks,
                                                            user_db_info.stocks *
                                                                stock_prices[i - 1].close };

                    int64_t stocks_to_process = ffi::evaluate_expression(exe,
                                                                         variables.data(),
                                                                         values.data(),
                                                                         variables.size(),
                                                                         error.data(),
                                                                         error.size());

                    LOG_INFO() << fmt::format("Balance: {}, Stock Price: {}, Stocks: {}, Holdings: "
                                              "{}. Strategy yields: {}",
                                              values[0],
                                              values[1],
                                              values[2],
                                              values[3],
                                              stocks_to_process);

                    if (stocks_to_process < 0) {
                        // Strategy wants to sell
                        if (user_db_info.stocks < -stocks_to_process) {
                            // Not enough stocks to sell
                            trade_status =
                                kTradeStatusStr[static_cast<uint32_t>(TradeStatus::kFailed)];
                            break;
                        }

                        user_db_info.stocks -= -stocks_to_process;
                        user_db_info.balance += -stocks_to_process * stock_prices[i].close;
                        net_profit += -stocks_to_process * stock_prices[i].close;
                    } else if (stocks_to_process > 0) {
                        // Strategy wants to buy
                        if (stocks_to_process * stock_prices[i].close < 0 ||
                            user_db_info.balance < stocks_to_process * stock_prices[i].close) {
                            // Not enough balance to buy
                            trade_status =
                                kTradeStatusStr[static_cast<uint32_t>(TradeStatus::kFailed)];
                            break;
                        }

                        user_db_info.stocks += stocks_to_process;
                        user_db_info.balance -= stocks_to_process * stock_prices[i].close;
                        net_profit -= stocks_to_process * stock_prices[i].close;
                    }
                }

                // Update the user's balance and stocks
                UpdateUserBalanceAndStocks(
                    user_db_info.username, user_db_info.balance, user_db_info.stocks);

                // Process the trade
                UpdateTradeByUUID(trade_id, net_profit, trade_status);

                LOG_INFO() << fmt::format("Trade {} processed with status: {}",
                                          boost::uuids::to_string(trade_id),
                                          trade_status);

                ffi::free_executable(exe);
            });

        return TradeSubmitResponseBody{ boost::uuids::to_string(trade_id), code_integrity };
    }
}}
