FROM alpine:3.15

RUN apk --no-cache add postgresql12-client
RUN adduser -H -s /bin/false -u 1000 -D clean
COPY clean.sh /clean.sh
COPY clean.sql /clean.sql
RUN chmod +x /clean.sh
USER clean
ENTRYPOINT ["/clean.sh"]