#!/bin/sh

redis-server /etc/redis/redis.conf &
cd /app && python3.12 main.py
