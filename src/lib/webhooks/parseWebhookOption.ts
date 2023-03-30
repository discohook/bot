import {
  AutoCompleteLimits,
  isCategoryChannel,
  isThreadChannel,
} from "@sapphire/discord.js-utilities"
import {
  BaseChannel,
  CategoryChannel,
  channelMention,
  ChatInputCommandInteraction,
  Guild,
  GuildBasedChannel,
} from "discord.js"
import { reply } from "../interactions/reply"
import { ellipsize } from "../lang/ellipsize"
import { fetchWebhooks } from "./fetchWebhooks"

export const parseWebhookOption = async (
  interaction: ChatInputCommandInteraction,
  webhookOptionName = "webhook",
  channelOptionName = "channel",
) => {
  let source: Guild | Exclude<GuildBasedChannel, CategoryChannel> =
    interaction.guild!

  const channel = interaction.options.getChannel(channelOptionName)
  if (channel instanceof BaseChannel && !isCategoryChannel(channel)) {
    source = isThreadChannel(channel)
      ? channel.parent ?? channel.guild
      : channel
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
