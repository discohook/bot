import type {
  ChatInputCommandInteraction,
  GuildEmoji,
  Message,
  ReactionEmoji,
} from "discord.js"
import { reply } from "../interactions/reply"
import { emojiNameToUnicodeMap } from "./emojiNameToUnicodeMap"
import { emojiUnicodeToNameMap } from "./emojiUnicodeToNameMap"

export const parseReactionOption = async (
  interaction: ChatInputCommandInteraction,
  emojiOptionName = "emoji",
  message?: Message,
): Promise<string | GuildEmoji | ReactionEmoji | undefined> => {
  const query = interaction.options.getString(emojiOptionName, true)

  const safeQuery = query.replace(/[\W-+]*/g, "")

  if (interaction.guild) {
    const emoji =
      interaction.guild.emojis.cache.get(safeQuery) ??
      interaction.guild.emojis.cache.find((emoji) => emoji.name === safeQuery)
    if (emoji) return emoji
  }

  if (message) {
    const reaction = message.reactions.cache.find(
      (reaction) => reaction.emoji.name === query,
    )

    if (reaction) return reaction.emoji
  }

  if (Object.prototype.hasOwnProperty.call(emojiUnicodeToNameMap, query)) {
    return query
  }

  if (Object.prototype.hasOwnProperty.call(emojiNameToUnicodeMap, safeQuery)) {
    return emojiNameToUnicodeMap[safeQuery]
  }

  await reply(interaction, {
    content: "The emoji could not be found.",
  })

  return
}
