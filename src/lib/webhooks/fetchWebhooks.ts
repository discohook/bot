import { AnyChannel, Guild, GuildChannel, TextBasedChannel } from "discord.js"

export const fetchWebhooks = async (
  source: Guild | Extract<Extract<AnyChannel, TextBasedChannel>, GuildChannel>,
) => {
  const guild = source instanceof Guild ? source : source.guild

  return [...(await source.fetchWebhooks()).values()]
    .filter((webhook) => webhook.isIncoming() && webhook.token)
    .sort((left, right) => {
      const leftChannel = guild.channels.cache.get(left.channelId)
      const rightChannel = guild.channels.cache.get(right.channelId)

      if (!(leftChannel instanceof GuildChannel)) return 0
      if (!(rightChannel instanceof GuildChannel)) return 0

      if (leftChannel.parent?.id === rightChannel.parent?.id) {
        return leftChannel.position - rightChannel.position
      }

      return (
        (leftChannel.parent?.position ?? 0) -
        (rightChannel.parent?.position ?? 0)
      )
    })
}
