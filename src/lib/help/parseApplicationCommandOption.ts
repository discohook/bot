import type { ChatInputCommandInteraction } from "discord.js"
import { reply } from "../interactions/reply"
import { getApplicationCommands } from "./getApplicationCommands"

export const parseApplicationCommandOption = async (
  interaction: ChatInputCommandInteraction,
  commandOptionName = "command",
) => {
  const query = interaction.options.getString(commandOptionName, true)

  for (const command of getApplicationCommands().values()) {
    if (query.slice(0, command.displayName.length) !== command.displayName) {
      continue
    }

    if (query[command.displayName.length] === ":") {
      return [command, undefined] as const
    }

    const possibleSubcommandName = query
      .slice(command.displayName.length + 1)
      .replace(/ ?[:<[].+/, "")

    for (const subcommand of command.subcommands) {
      if (subcommand.name === possibleSubcommandName) {
        return [command, subcommand.name] as const
      }
    }
  }

  await reply(interaction, {
    content: "The command could not be found.",
  })

  return
}
