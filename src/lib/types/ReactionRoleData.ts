import type { Snowflake } from "discord-api-types/v9"

export type ReactionRoleData = {
  message_id: Snowflake
  channel_id: Snowflake
  guild_id: Snowflake
  role_id: Snowflake
  reaction: string
}
