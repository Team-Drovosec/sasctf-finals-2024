cmake_minimum_required(VERSION 3.12)
set(CMAKE_CXX_STANDARD 20)
project(trusted_trading CXX)

# Make sure our binary is not position-independent (simplifies exploitation)
add_compile_options(-fno-pic -no-pie)
add_link_options(-no-pie)

# Adding userver dependency
find_package(userver COMPONENTS core postgresql QUIET)
find_package(Boost COMPONENTS random REQUIRED)

if(NOT userver_FOUND) # Fallback to subdirectory usage
    # Compatibility mode: some systems don't support these features
    set(USERVER_FEATURE_CRYPTOPP_BLAKE2 OFF CACHE BOOL "" FORCE)
    set(USERVER_FEATURE_GRPC_CHANNELZ OFF CACHE BOOL "" FORCE)
    set(USERVER_FEATURE_REDIS_HI_MALLOC ON CACHE BOOL "" FORCE)
    set(USERVER_FEATURE_POSTGRESQL ON CACHE BOOL "" FORCE)

    if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/third_party/userver)
        message(STATUS "Using userver framework from third_party/userver")
        add_subdirectory(third_party/userver)
    else()
        message(FATAL_ERROR "Either install the userver or provide a path to it")
    endif()
endif()

userver_setup_environment()

# Rust Math-Evaluator
add_library(math_evaluator STATIC IMPORTED)
add_custom_target(math_evaluator_cargo
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/spark-jit/
    COMMAND cargo build --release
)
set(MATH_EVALUATOR_LIB ${CMAKE_CURRENT_SOURCE_DIR}/spark-jit/target/release/libmath_evaluator.a)
set_target_properties(math_evaluator PROPERTIES IMPORTED_LOCATION ${MATH_EVALUATOR_LIB})
add_dependencies(math_evaluator math_evaluator_cargo)

# Common sources
add_library(${PROJECT_NAME}_objs OBJECT
    src/middlewares/auth_middleware.cpp
    src/jwt_key_generator.cpp
    src/endpoints/register.cpp
    src/endpoints/trade_history.cpp
    src/endpoints/user_trade_submit.cpp
    src/endpoints/user_trade_status.cpp
    src/endpoints/login.cpp
    src/endpoints/stock_price.cpp
    src/endpoints/user_info.cpp
)
target_link_libraries(${PROJECT_NAME}_objs PUBLIC userver::core Boost::random userver::postgresql math_evaluator)
target_compile_options(${PROJECT_NAME}_objs PRIVATE -fno-pic -no-pie)
target_include_directories(${PROJECT_NAME}_objs PUBLIC src)

# JWT-CPP
target_include_directories(${PROJECT_NAME}_objs PUBLIC third_party/include)

include(ChaoticGen)

# Generate JSONSchema serializers
file(GLOB_RECURSE SCHEMAS ${CMAKE_CURRENT_SOURCE_DIR}/schemas/*.yaml)
message(STATUS "Found JSONSchema files: ${SCHEMAS}")
userver_target_generate_chaotic(${PROJECT_NAME}-chgen
    ARGS

    # Map '/components/schemas/*' JSONSchema types to C++ types in 'trusted_trading' namespace
    -n "/components/schemas/([^/]*)/=tt::{0}"
    -f "(.*)={0}"

    # Don't call clang-format
    --clang-format=
    --generate-serializers
    OUTPUT_DIR
    ${CMAKE_CURRENT_BINARY_DIR}/src
    SCHEMAS
    ${SCHEMAS}
    RELATIVE_TO
    ${CMAKE_CURRENT_SOURCE_DIR}
)
target_link_libraries(${PROJECT_NAME}_objs PUBLIC ${PROJECT_NAME}-chgen)

# The Service
add_executable(${PROJECT_NAME} src/main.cpp)
target_compile_options(${PROJECT_NAME} PRIVATE -fno-pic -no-pie)
target_link_libraries(${PROJECT_NAME} PRIVATE ${PROJECT_NAME}_objs)

# Unit Tests
add_executable(${PROJECT_NAME}_unittest
    src/tests/trusted_trading.cpp
)
target_link_libraries(${PROJECT_NAME}_unittest PRIVATE ${PROJECT_NAME}_objs userver::utest)
add_google_tests(${PROJECT_NAME}_unittest)

# Benchmarks
add_executable(${PROJECT_NAME}_benchmark
    src/benchmarks/trusted_trading.cpp
)
target_link_libraries(${PROJECT_NAME}_benchmark PRIVATE ${PROJECT_NAME}_objs userver::ubench)
add_google_benchmark_tests(${PROJECT_NAME}_benchmark)

# Functional Tests
include(UserverTestsuite)

userver_testsuite_add_simple()

# Install
include(GNUInstallDirs)

if(DEFINED ENV{PREFIX})
    message(STATUS "Set install prefix: $ENV{PREFIX}")
    file(TO_CMAKE_PATH "$ENV{PREFIX}" PREFIX_PATH)
    set(CMAKE_INSTALL_PREFIX "${PREFIX_PATH}")
endif()

file(GLOB CONFIGS_FILES ${CMAKE_CURRENT_SOURCE_DIR}/configs/*.yaml ${CMAKE_CURRENT_SOURCE_DIR}/configs/*.json)

install(TARGETS ${PROJECT_NAME} DESTINATION ${CMAKE_INSTALL_BINDIR} COMPONENT ${PROJECT_NAME})
install(FILES ${CONFIGS_FILES} DESTINATION ${CMAKE_INSTALL_SYSCONFDIR}/${PROJECT_NAME} COMPONENT ${PROJECT_NAME})
