CREATE TABLE guild_config (
  guild_id BIGINT NOT NULL PRIMARY KEY,
  prefix TEXT NOT NULL DEFAULT 'd.'
);
