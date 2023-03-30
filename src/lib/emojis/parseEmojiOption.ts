import {
  APIPartialEmoji,
  ChatInputCommandInteraction,
  FormattingPatterns,
  GuildEmoji,
} from "discord.js"
import { reply } from "../interactions/reply"
import { emojiNameToUnicodeMap } from "./emojiNameToUnicodeMap"
import { emojiUnicodeToNameMap } from "./emojiUnicodeToNameMap"

export const parseEmojiOption = async (
  interaction: ChatInputCommandInteraction,
  emojiOptionName = "emoji",
): Promise<string | GuildEmoji | APIPartialEmoji | undefined> => {
  const query = interaction.options.getString(emojiOptionName, true)

  const safeQuery = query.replace(/[\W-+]*/g, "")

  if (interaction.guild) {
    const emoji =
      interaction.guild.emojis.cache.get(safeQuery) ??
      interaction.guild.emojis.cache.find((emoji) => emoji.name === safeQuery)
    if (emoji) return emoji
  }

  const match = FormattingPatterns.Emoji.exec(query)
  if (match) {
    return {
      id: match.groups!.id,
      name: match.groups!.name,
      animated: Boolean(match.groups!.animated),
    } as APIPartialEmoji
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
