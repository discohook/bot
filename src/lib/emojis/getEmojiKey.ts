import type { APIPartialEmoji } from "discord-api-types/v9"
import type { Emoji } from "discord.js"

export const getEmojiKey = (emoji: string | Emoji | APIPartialEmoji) => {
  if (typeof emoji === "object") return emoji.id ?? emoji.name!
  return emoji
}
