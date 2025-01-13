/* /// [postgresql schema] */
DROP SCHEMA IF EXISTS trusted_trading CASCADE;

CREATE SCHEMA IF NOT EXISTS trusted_trading;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE EXTENSION pgcrypto;

CREATE TABLE IF NOT EXISTS trusted_trading.users (
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    balance BIGINT NOT NULL DEFAULT 100000,
    stocks BIGINT NOT NULL DEFAULT 1,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY(username)
);

CREATE TABLE IF NOT EXISTS trusted_trading.trades (
    trade_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username TEXT NOT NULL,
    net_profit BIGINT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    strategy TEXT,
    strategy_integrity TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (username) REFERENCES trusted_trading.users(username) ON DELETE CASCADE
);

/* /// [postgresql schema] */