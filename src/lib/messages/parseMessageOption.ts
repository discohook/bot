import {
  BaseGuildTextChannel,
  CommandInteraction,
  ThreadChannel,
} from "discord.js"
import { reply } from "../interactions/reply"

export const parseMessageOption = async (
  interaction: CommandInteraction,
  messageOptionName = "message",
) => {
  const query = interaction.options.getString(messageOptionName, true)

  const result =
    /^https?:\/\/(?:www\.|ptb\.|canary\.)?discord\.com\/channels\/(\d+)\/(\d+)\/(\d+)$/.exec(
      query,
    )

  if (!result) {
    await reply(interaction, {
      content: "The message provided is not a valid message link.",
    })
    return
  }

  const [, guildId, channelId, messageId] = result
  if (guildId !== interaction.guild?.id) {
    await reply(interaction, {
      content: "The message provided isn't from this server.",
    })
    return
  }

  const channel = interaction.guild.channels.cache.get(channelId)
  if (!channel) {
    await reply(interaction, {
      content: "The message provided is from a non-existing channel.",
    })
    return
  }

  if (
    !(channel instanceof BaseGuildTextChannel) &&
    !(channel instanceof ThreadChannel)
  ) {
    await reply(interaction, {
      content:
        "The channel this message link belongs to does not support reaction roles.",
    })
    return
  }

  const missingPerms = channel
    .permissionsFor(interaction.guild.me!)
    .missing(["VIEW_CHANNEL", "READ_MESSAGE_HISTORY"])
  if (missingPerms.length > 0) {
    await reply(interaction, {
      content:
        "I'm missing permission to read messages in this channel. Make sure I can view the channel and read the message history.",
    })
    return
  }

  try {
    return await channel.messages.fetch(messageId)
  } catch {
    await reply(interaction, {
      content: "This message does not exist.",
    })
    return
  }
}
