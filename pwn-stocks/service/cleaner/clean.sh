#!/bin/sh

while true; do
    echo "Cleaning up the database"
    psql postgresql://trusted_trading:password@postgres:5432/pg_trusted_trading_db -f /clean.sql
    sleep 300
done