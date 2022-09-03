import type { Guild } from "discord.js"

export const getSelf = async (guild: Guild) => {
  if (!guild.me || guild.me.partial) {
    return guild.members.fetch(guild.client.user?.id!)
  }
  if (guild.me.permissions.bitfield === 0n) {
    // This smells, but zero permissions is very unusual and a good sign the
    // cache is messed up.
    await guild.fetch()
    return guild.members.fetch({ user: guild.client.user?.id!, force: true })
  }
  return guild.me
}
