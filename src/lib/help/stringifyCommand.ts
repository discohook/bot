import { bold } from "discord.js"
import type { CommandHelpData } from "./CommandHelpData"

type FormatCommandOptions = {
  markdown?: boolean
  includeSubCommands?: boolean
}

export const stringifyCommand = (
  command: CommandHelpData,
  options?: FormatCommandOptions,
) => {
  const { markdown = true, includeSubCommands = false } = options ?? {}

  let commandString = command.displayName
  for (const option of command.arguments) {
    commandString += option.required ? ` <${option.name}>` : ` [${option.name}]`
  }

  if (markdown) commandString = bold(commandString)

  commandString += ": " + command.description

  if (includeSubCommands) {
    for (const subcommand of command.subcommands) {
      let subCommandString = command.displayName + " " + subcommand.name
      for (const option of subcommand.arguments) {
        subCommandString += option.required
          ? ` <${option.name}>`
          : ` [${option.name}]`
      }

      if (markdown) subCommandString = bold(subCommandString)

      subCommandString += ": " + subcommand.description

      commandString += "\n" + subCommandString
    }
  }

  return commandString
}
