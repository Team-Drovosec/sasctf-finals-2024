DELETE FROM
    users
WHERE
    created_at < NOW() - INTERVAL '30 minutes';
    
DELETE FROM
    beers
WHERE
    timestamp < NOW() - INTERVAL '30 minutes';
    
DELETE FROM
    comments
WHERE
    timestamp < NOW() - INTERVAL '30 minutes';
