#include "stock_price.hpp"

namespace tt { namespace endpoints {
    std::unique_ptr<StockPriceGenerator> g_stock_price_generator_{ nullptr };

    StockPriceResponseBody StockPriceHandler::StockPrice(StockPriceRequestBody& request) const
    {
        StockPriceResponseBody response;

        const auto stock_prices = g_stock_price_generator_->GetStockPrices();

        std::transform(stock_prices.rbegin(),
                       std::min(stock_prices.rbegin() + request.limit.value_or(stock_prices.size()),
                                stock_prices.rend()),
                       std::back_inserter(response.prices),
                       [](const StockPriceGenerator::StockPrice& price) {
                           return StockPriceResponseBody::PricesA{
                               std::to_string(price.timestamp.time_since_epoch().count()),
                               price.open,
                               price.close,
                               price.high,
                               price.low
                           };
                       });

        return response;
    }
}}