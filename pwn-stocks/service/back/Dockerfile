FROM ubuntu:22.04

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update -y && apt-get install -y build-essential ccache cmake git libabsl-dev libbenchmark-dev libboost-random1.74.0 libboost-random1.74-dev libboost-context1.74-dev libboost-coroutine1.74-dev libboost-filesystem1.74-dev libboost-iostreams1.74-dev libboost-locale1.74-dev libboost-program-options1.74-dev libboost-regex1.74-dev libboost-stacktrace1.74-dev libboost1.74-dev libbson-dev libbz2-dev libc-ares-dev libcctz-dev libcrypto++-dev libcurl4-openssl-dev libdouble-conversion-dev libev-dev libfmt-dev libgflags-dev libgmock-dev libgrpc++-dev libgrpc++1 libgrpc-dev libgtest-dev libhiredis-dev libidn11-dev libjemalloc-dev libkrb5-dev libldap2-dev librdkafka-dev liblz4-dev libmariadb-dev libmongoc-dev libnghttp2-dev libpq-dev libprotoc-dev libsnappy-dev libsasl2-dev libssl-dev libxxhash-dev libyaml-cpp-dev libzstd-dev netbase ninja-build postgresql-server-dev-14 ragel zlib1g-dev
RUN useradd --no-create-home --shell /bin/false --uid 1000 --user-group trusted_trading
RUN mkdir -p /var/trusted_trading/games && chown -R trusted_trading:trusted_trading /var/trusted_trading
COPY trusted_trading /
COPY configs /configs
RUN chmod +x /trusted_trading
USER trusted_trading
ENTRYPOINT ["/trusted_trading", "-c", "/configs/static_config.yaml", "--config_vars", "/configs/config_vars.yaml"]