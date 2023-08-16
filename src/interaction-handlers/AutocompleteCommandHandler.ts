import { AutoCompleteLimits } from "@sapphire/discord-utilities"
import {
  InteractionHandler,
  InteractionHandlerTypes,
  type PieceContext,
} from "@sapphire/framework"
import type { AutocompleteInteraction } from "discord.js"
import { getApplicationCommands } from "../lib/help/getApplicationCommands"
import { stringifyCommand } from "../lib/help/stringifyCommand"
import { ellipsize } from "../lib/lang/ellipsize"

type AutocompleteCommandOptions = {
  query: string
}

export class AutocompleteCommandHandler extends InteractionHandler {
  constructor(context: PieceContext) {
    super(context, {
      name: "autocomplete-command",
      interactionHandlerType: InteractionHandlerTypes.Autocomplete,
    })
  }

  override async run(
    interaction: AutocompleteInteraction,
    options: AutocompleteCommandOptions,
  ) {
    const words = options.query.toLocaleLowerCase().split(/\s+/)

    await interaction.respond(
      Array.from(getApplicationCommands().values())
        .flatMap((command) =>
          stringifyCommand(command, {
            markdown: false,
            includeSubCommands: true,
          }).split("\n"),
        )
        .filter((formatted) =>
          words.every((word) => formatted.toLocaleLowerCase().includes(word)),
        )
        .map((formatted) =>
          ellipsize(formatted, AutoCompleteLimits.MaximumLengthOfNameOfOption),
        )
        .map((formatted) => ({
          name: formatted,
          value: formatted,
        }))
        .slice(0, AutoCompleteLimits.MaximumAmountOfOptions),
    )
  }

  override async parse(interaction: AutocompleteInteraction) {
    const { name, value } = interaction.options.getFocused(true)
    if (name !== "command") return this.none()

    return this.some<AutocompleteCommandOptions>({ query: String(value) })
  }
}
