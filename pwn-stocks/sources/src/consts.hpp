#pragma once

#include <string>

namespace tt::consts {
    const static std::string kBasePath = "/var/trusted_trading/";
    constexpr std::size_t kMinPasswordLength = 8;
    constexpr std::size_t kMaxPasswordLength = 64;

    constexpr std::size_t kMaxUsernameLength = 64;
}