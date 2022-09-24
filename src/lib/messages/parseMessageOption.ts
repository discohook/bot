import type { CommandInteraction } from "discord.js"
import { reply } from "../interactions/reply"

export const parseMessageOption = async (
  interaction: CommandInteraction,
  messageOptionName = "message",
) => {
  const query = interaction.options.getString(messageOptionName, true)

  const result =
      /^https?:\/\/(?:www\.|ptb\.|canary\.)?discord(?:app)?\.com\/channels\/(\d+)\/(\d+)\/(\d+)$/.exec(
      query,
    )

  if (!result) {
    await reply(interaction, {
      content: "The message provided is not a valid message link.",
    })
    return [] as const
  }

  const [, guildId, channelId, messageId] = result
  if (guildId !== interaction.guild?.id) {
    await reply(interaction, {
      content: "The message provided isn't from this server.",
    })
    return [] as const
  }

  return [channelId, messageId] as const
}
