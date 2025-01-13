-- +goose Up
-- +goose StatementBegin
create table users (
        id bigserial primary key,
        description text,

        username text,
        password bytea
);

create unique index on users (username);

create table koshechko (
    id bigserial primary key,
    name text,
    owner text,
    text text,
    shared_with text[]
);

create unique index on koshechko(name);

create table lb_queue (
    id bigserial primary key,
    type int4,
    username text,
    koshechko_name text,
    shared_count bigint,
    koshechko_new_name text,
    koshechko_text text,
    koshechko_shared_with text[],

    created_at timestamptz not null default now()
);

create index on lb_queue(created_at);


-- create table friend_points (
--     name_from text REFERENCES users(username) ON DELETE CASCADE,
--     name_to text REFERENCES users(username) ON DELETE CASCADE,

--     share_count int
-- );


-- -- создание кошечки
-- (в ручке синхронно проверим например что юзеры которым шерится действительно существуют)
-- creat koshechch: -> ETIncFriends -> outbox
-- delete user: -> del user
-- worker: -> upsert increment +1 friend_points -> insert будет фейлиться если name_from или name_to уже удален -> фейлится батч и транзакция -> временно доступны кошечки



-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
-- +goose StatementEnd
