import {
  BaseCommandInteraction,
  MessageComponentInteraction,
  Permissions,
} from "discord.js"
import { getSelf } from "../guilds/getSelf"
import { reply } from "../interactions/reply"

export const fetchMessage = async (
  interaction: BaseCommandInteraction | MessageComponentInteraction,
  channelId: string,
  messageId: string,
) => {
  const channel = interaction.client.channels.cache.get(channelId)
  if (!channel) {
    await reply(interaction, {
      content:
        "The message is from a channel I can't see. If the message is in an " +
        "archived thread please unarchive it to make sure I can read it.",
    })
    return
  }

  if (!channel.isText()) {
    await reply(interaction, {
      content: "The channel the message belongs to does not support messages.",
    })
    return
  }

  const selfPermissions =
    "guild" in channel && channel.guild
      ? channel.permissionsFor(await getSelf(channel.guild))
      : new Permissions(Permissions.DEFAULT)

  const missingPerms = selfPermissions.missing([
    "VIEW_CHANNEL",
    "READ_MESSAGE_HISTORY",
  ])
  if (missingPerms.length > 0) {
    await reply(interaction, {
      content:
        "I'm missing permission to read messages in the channel. Make sure " +
        "I can view the channel and read the message history.",
    })
    return
  }

  try {
    return await channel.messages.fetch(messageId)
  } catch {
    await reply(interaction, {
      content: "The message could not be found.",
    })
    return
  }
}
