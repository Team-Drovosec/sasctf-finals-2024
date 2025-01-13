#pragma once
#include <consts.hpp>
#include <string>

namespace tt {
    class JWTKeyGenerator final
    {
    public:
        const std::string& GenerateOrGetPrivateKey();

        static JWTKeyGenerator& GetInstance()
        {
            static JWTKeyGenerator instance;
            return instance;
        }

        inline static const std::string issuer = "sasno";

    private:
        const std::string kPrivateKeyPath = consts::kBasePath + "/jwt_key";
        std::string private_key_;
    };
}
