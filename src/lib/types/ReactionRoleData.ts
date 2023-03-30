import type { Snowflake } from "discord.js"

export type ReactionRoleData = {
  message_id: Snowflake
  channel_id: Snowflake
  guild_id: Snowflake
  role_id: Snowflake
  reaction: string
}
