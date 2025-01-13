DELETE FROM
    trusted_trading.trades
WHERE
    trades.timestamp < NOW() - INTERVAL '30 minutes';

DELETE FROM
    trusted_trading.users
WHERE
    users.timestamp < NOW() - INTERVAL '30 minutes';