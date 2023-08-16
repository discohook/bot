import { isThreadChannel } from "@sapphire/discord.js-utilities"
import {
  CategoryChannel,
  Guild,
  type GuildBasedChannel,
  GuildChannel,
} from "discord.js"

export const fetchWebhooks = async (
  source: Guild | Exclude<GuildBasedChannel, CategoryChannel>,
) => {
  const guild = source instanceof Guild ? source : source.guild

  if (!(source instanceof Guild) && isThreadChannel(source)) {
    source = source.parent ?? source.guild
  }

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
