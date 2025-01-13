#!/bin/sh

while true; do
    echo "Cleaning up the database"
    psql postgresql://postgres:123@postgres:5432/beerloga -f /clean.sql
    sleep 300
done
