#pragma once

#include <chrono>
#include <cmath>
#include <random>
#include <shared_mutex>
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
#include "userver/engine/shared_mutex.hpp"
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

    class StockPriceGenerator
    {
    public:
        struct StockPrice
        {
            int64_t open{};
            int64_t close{};
            int64_t high{};
            int64_t low{};
            std::chrono::system_clock::time_point timestamp;
        };

        StockPriceGenerator()
            : rng_(std::random_device{}())
        {
            auto now = std::chrono::system_clock::now() - std::chrono::seconds{ kMaxEntries };

            StockPrice first_price;
            first_price.open = GenerateRandomPrice();
            first_price.close = GenerateRandomPrice();
            first_price.high = std::max(first_price.open, first_price.close);
            first_price.low = std::min(first_price.open, first_price.close);
            first_price.timestamp = now;
            stock_prices_.push_back(first_price);

            while (stock_prices_.size() < kMaxEntries) {
                now += std::chrono::seconds{ 1 };
                UpdateStockPrices(now);
            }
        }

        void UpdateStockPrices(
            std::chrono::system_clock::time_point timestamp = std::chrono::system_clock::now())
        {
            std::lock_guard lock(mutex_);
            if (stock_prices_.size() >= kMaxEntries)
                stock_prices_.pop_front();

            StockPrice new_price;
            new_price.open = stock_prices_.back().close;
            new_price.close = GenerateRandomPrice();
            new_price.high = GenerateRandomInRange(new_price.close, new_price.close + 20);
            new_price.low = GenerateRandomInRange(new_price.close - 36, new_price.close);
            new_price.timestamp = timestamp;

            stock_prices_.push_back(new_price);
        }

        std::deque<StockPrice> GetStockPrices()
        {
            std::shared_lock lock(mutex_);
            return stock_prices_;
        }

    private:
        constexpr static int64_t kMean = 150;
        constexpr static int64_t kStd = 40;
        constexpr static uint32_t kMaxEntries = 100;

        int64_t GenerateRandomInRange(int64_t min, int64_t max)
        {
            std::uniform_int_distribution<int64_t> dist(min, max);
            return dist(rng_);
        }

        int64_t GenerateRandomPrice()
        {
            std::normal_distribution<float> price_dist(kMean, kStd);
            return static_cast<int64_t>(std::round(price_dist(rng_)));
        }

        engine::SharedMutex mutex_;
        std::deque<StockPrice> stock_prices_;
        // Random number generator
        std::mt19937_64 rng_;
    };

    extern std::unique_ptr<StockPriceGenerator> g_stock_price_generator_;

    class StockPriceHandler : public server::handlers::HttpHandlerJsonBase
    {
    public:
        static constexpr std::string_view kName = "handler-stock-price";

        StockPriceHandler(const components::ComponentConfig& config,
                          const components::ComponentContext& context)
            : HttpHandlerJsonBase(config, context)
        {
            g_stock_price_generator_ = std::make_unique<StockPriceGenerator>();
            stock_price_generator_task_.Start(
                "stock_price_generator_task", std::chrono::seconds{ 1 }, []() {
                    g_stock_price_generator_->UpdateStockPrices();
                });
        }

        json::Value HandleRequestJsonThrow(
            const server::http::HttpRequest& /*request*/,
            const json::Value& json,
            server::request::RequestContext& /*context*/) const override
        {
            try {
                auto request_dom = json.As<StockPriceRequestBody>();
                auto response_dom = StockPrice(request_dom);
                auto response_json = json::ValueBuilder{ response_dom }.ExtractValue();
                return response_json;
            } catch (const json::ExceptionWithPath& ex) {
                throw utils::PrepareJsonError(ex.GetMessage());
            }
        }

    private:
        StockPriceResponseBody StockPrice(StockPriceRequestBody& request) const;

        userver::utils::PeriodicTask stock_price_generator_task_;
    };
}}