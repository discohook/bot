import { channelMention } from "@discordjs/builders"
import { AutoCompleteLimits } from "@sapphire/discord.js-utilities"
import {
  AnyChannel,
  Channel,
  CommandInteraction,
  Guild,
  GuildChannel,
  TextBasedChannel,
} from "discord.js"
import { reply } from "../interactions/reply"
import { ellipsize } from "../lang/ellipsize"
import { fetchWebhooks } from "./fetchWebhooks"

export const parseWebhookOption = async (
  interaction: CommandInteraction,
  webhookOptionName = "webhook",
  channelOptionName = "channel",
) => {
  let source:
    | Guild
    | Extract<Extract<AnyChannel, TextBasedChannel>, GuildChannel> =
    interaction.guild!

  const channel = interaction.options.getChannel(channelOptionName)
  if (channel instanceof Channel && channel.isText()) {
    source = channel.isThread() ? channel.parent ?? interaction.guild! : channel
  }

  const webhooks = await fetchWebhooks(source)

  const query = interaction.options.getString(webhookOptionName, true)
  if (/^\d+$/.test(query)) {
    const webhook = webhooks.find((webhook) => webhook.id === query)
    if (webhook) return webhook
  }

  const candidates = webhooks.filter((webhook) => {
    const channel = interaction.guild!.channels.cache.get(webhook.channelId)!

    return [
      `#${channel.name}: ${webhook.name}`.toLocaleLowerCase(),
      `${channelMention(channel.id)}: ${webhook.name}`.toLocaleLowerCase(),
      webhook.name.toLocaleLowerCase(),
    ]
      .map((value) =>
        ellipsize(value, AutoCompleteLimits.MaximumLengthOfNameOfOption),
      )
      .includes(query.toLocaleLowerCase())
  })

  if (candidates.length === 0) {
    await reply(interaction, {
      content: "The webhook could not be found.",
    })
    return
  }

  if (candidates.length > 1) {
    await reply(interaction, {
      content:
        "There are multiple webhooks with this name, try using the Webhook ID, which can be found with **/webhook list show-ids: true**.",
    })
    return
  }

  return candidates[0]
}
