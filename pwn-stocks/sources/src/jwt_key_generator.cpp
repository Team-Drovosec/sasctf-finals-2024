#include "jwt_key_generator.hpp"
#include <filesystem>
#include <string>

#include "userver/fs/blocking/read.hpp"
#include "userver/fs/blocking/write.hpp"
#include <fmt/format.h>
#include <openssl/rand.h>

namespace tt {
    using namespace userver;

    const std::string& JWTKeyGenerator::GenerateOrGetPrivateKey()
    {
        if (!private_key_.empty()) {
            return private_key_;
        }

        if (!fs::blocking::FileExists(consts::kBasePath)) {
            fs::blocking::CreateDirectories(consts::kBasePath, boost::filesystem::perms::owner_all);
        }

        if (fs::blocking::FileExists(kPrivateKeyPath)) {
            private_key_ = fs::blocking::ReadFileContents(kPrivateKeyPath);
            return private_key_;
        }

        constexpr size_t kKeySize = 64;
        std::vector<uint8_t> key(kKeySize, '\0');
        if (RAND_bytes(reinterpret_cast<unsigned char*>(key.data()), kKeySize) != 1) {
            throw std::runtime_error("Failed to generate a private key");
        }

        std::string hex_key;
        for (const auto& byte : key) {
            hex_key += fmt::format("{:02x}", byte);
        }

        private_key_ = hex_key;

        fs::blocking::RewriteFileContents(kPrivateKeyPath, hex_key);
        return private_key_;
    }

}
