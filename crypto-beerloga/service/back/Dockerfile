FROM ubuntu:22.04

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update -y

RUN apt install -y wget gnustep-make gcc g++ gobjc gnustep gnustep-devel libblocksruntime0
RUN apt install -y postgresql-client

RUN apt install -y socat

RUN useradd --no-create-home --shell /bin/false --uid 1000 --user-group beerloga
COPY beerloga /
COPY beerloga-client /
RUN chmod +x /beerloga


# RUN apt install -y libgnustep-base1.26 postgresql-client
COPY libs/* /usr/lib/

ENTRYPOINT socat tcp-l:3000,reuseaddr,fork EXEC:"timeout -s 9 120s /beerloga"

# USER beerloga
# ENTRYPOINT /beerloga
