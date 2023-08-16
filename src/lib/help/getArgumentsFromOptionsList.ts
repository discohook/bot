import {
  ApplicationCommandOptionType,
  type ApplicationCommandOption,
  type ApplicationCommandSubCommand,
  type ApplicationCommandSubGroup,
} from "discord.js"
import type { ArgumentHelpData } from "./CommandHelpData"

export const getArgumentsFromOptionsList = (
  options: readonly ApplicationCommandOption[] = [],
): ArgumentHelpData[] => {
  return options
    .filter(
      (
        option,
      ): option is Exclude<
        typeof option,
        ApplicationCommandSubGroup | ApplicationCommandSubCommand
      > =>
        ![
          ApplicationCommandOptionType.Subcommand,
          ApplicationCommandOptionType.SubcommandGroup,
        ].includes(option.type),
    )
    .map((option) => ({
      name: option.name,
      description: option.description,
      required: option.required ?? false,
    }))
}
