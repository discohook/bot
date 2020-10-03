CREATE TABLE reaction_role (
  message_id BIGINT NOT NULL,
  channel_id BIGINT NOT NULL,
  guild_id BIGINT NOT NULL REFERENCES guild_config ON DELETE CASCADE,
  role_id BIGINT NOT NULL,
  reaction TEXT NOT NULL,
  PRIMARY KEY (message_id, reaction)
);
