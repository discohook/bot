CREATE TABLE reaction_role (
  message_id BIGINT NOT NULL PRIMARY KEY,
  guild_id BIGINT NOT NULL REFERENCES guild_config ON DELETE CASCADE,
  role_id BIGINT NOT NULL,
  emoji TEXT NOT NULL
);
