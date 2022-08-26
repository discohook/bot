import { AutoCompleteLimits } from "@sapphire/discord-utilities"
import {
  InteractionHandler,
  InteractionHandlerTypes,
  PieceContext,
} from "@sapphire/framework"
import type { AutocompleteInteraction, Guild } from "discord.js"
import { emojiNameToUnicodeMap } from "../lib/emojis/emojiNameToUnicodeMap"

type AutocompleteEmojiOptions = {
  query: string
}

export class AutocompleteWebhookHandler extends InteractionHandler {
  constructor(context: PieceContext) {
    super(context, {
      name: "autocomplete-emoji",
      interactionHandlerType: InteractionHandlerTypes.Autocomplete,
    })
  }

  override async run(
    interaction: AutocompleteInteraction,
    options: AutocompleteEmojiOptions,
  ) {
    const guild = interaction.guild as Guild

    const words = options.query.toLocaleLowerCase().split(/\s+/)

    await interaction.respond(
      guild.emojis.cache
        .map((emoji) => ({
          name: emoji.name!,
          value: emoji.id,
        }))
        .concat(
          Object.entries(emojiNameToUnicodeMap).map(([name, value]) => ({
            name: `${value} ${name}`,
            value,
          })),
        )
        .filter((entry) =>
          words.every((word) => entry.name.toLocaleLowerCase().includes(word)),
        )
        .filter(
          (entry, index, array) =>
            array.findIndex((item) => item.value === entry.value) === index,
        )
        .slice(0, AutoCompleteLimits.MaximumAmountOfOptions),
    )
  }

  override async parse(interaction: AutocompleteInteraction) {
    if (!interaction.inGuild()) return this.none()

    const { name, value } = interaction.options.getFocused(true)

    if (
      name !== "emoji" &&
      (!["format", "image"].includes(interaction.commandName) ||
        interaction.options.getSubcommand() !== "emoji")
    )
      return this.none()

    return this.some<AutocompleteEmojiOptions>({
      query: String(value),
    })
  }
}
