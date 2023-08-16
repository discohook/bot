import {
  ApplicationCommandOptionType,
  type ApplicationCommandOption,
  type ApplicationCommandSubCommand,
  type ApplicationCommandSubGroup,
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
      > =>
        [
          ApplicationCommandOptionType.Subcommand,
          ApplicationCommandOptionType.SubcommandGroup,
        ].includes(option.type),
    )
    .flatMap((command) =>
      command.type === ApplicationCommandOptionType.SubcommandGroup
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
