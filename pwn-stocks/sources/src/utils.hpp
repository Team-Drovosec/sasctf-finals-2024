#pragma once

#include <boost/uuid/string_generator.hpp>
#include <string_view>
#include <userver/server/handlers/json_error_builder.hpp>

namespace tt { namespace utils {
    inline userver::server::handlers::ClientError PrepareJsonError(const std::string_view message)
    {
        return userver::server::handlers::ClientError{ userver::server::handlers::JsonErrorBuilder{
            "400", "", message } };
    }

    inline bool IsValidUuid(const std::string& uuid_str)
    {
        boost::uuids::string_generator gen;
        try {
            [[maybe_unused]] boost::uuids::uuid uuid = gen(uuid_str);
            return true; // Parsing succeeded, it's a valid UUID
        } catch (const std::runtime_error&) {
            return false; // Parsing failed, it's not a valid UUID
        }
    }
}}