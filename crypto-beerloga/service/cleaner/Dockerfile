FROM ubuntu:20.04

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update -y

RUN apt install -y wget gnustep-make gcc g++ gobjc gnustep gnustep-devel libblocksruntime0
RUN apt install -y postgresql-client

COPY libs/* /usr/lib/


COPY clean.sh /clean.sh
COPY clean.sql /clean.sql

RUN chmod +x /clean.sh
# RUN apk add libgnustep

ENTRYPOINT ["/clean.sh"]
