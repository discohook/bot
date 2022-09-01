import type { Guild } from "discord.js"

export const getSelf = async (guild: Guild) => {
  if (!guild.me || guild.me.partial) {
    return guild.members.fetch(guild.client.user?.id!)
  }
  return guild.me
}
