import type {
  ApplicationCommandOption,
  ApplicationCommandSubCommand,
  ApplicationCommandSubGroup,
} from "discord.js"
import type { ArgumentHelpData } from "./CommandHelpData"

export const getArgumentsFromOptionsList = (
  options: ApplicationCommandOption[] = [],
): ArgumentHelpData[] => {
  return options
    .filter(
      (
        option,
      ): option is Exclude<
        typeof option,
        ApplicationCommandSubGroup | ApplicationCommandSubCommand
      > =>
        !["SUB_COMMAND", "SUB_COMMAND_GROUP"].includes(option.type as string),
    )
    .map((option) => ({
      name: option.name,
      description: option.description,
      required: option.required ?? false,
    }))
}
