import type {
  ApplicationCommandOption,
  ApplicationCommandSubCommand,
  ApplicationCommandSubGroup,
} from "discord.js"
import type { SubcommandHelpData } from "./CommandHelpData"
import { getArgumentsFromOptionsList } from "./getArgumentsFromOptionsList"

export const getSubcommandsFromOptionsList = (
  options: ApplicationCommandOption[],
): SubcommandHelpData[] => {
  return options
    .filter(
      (
        option,
      ): option is Extract<
        typeof option,
        ApplicationCommandSubGroup | ApplicationCommandSubCommand
      > => ["SUB_COMMAND", "SUB_COMMAND_GROUP"].includes(option.type as string),
    )
    .flatMap((command) =>
      command.type === "SUB_COMMAND_GROUP"
        ? [
            {
              name: command.name,
              description: command.description,
              arguments: [],
            },
            ...(command.options?.map((subcommand) => ({
              name: command.name + " " + subcommand.name,
              description: subcommand.description,
              arguments: getArgumentsFromOptionsList(subcommand.options),
            })) ?? []),
          ]
        : [
            {
              name: command.name,
              description: command.description,
              arguments: getArgumentsFromOptionsList(command.options),
            },
          ],
    )
}
