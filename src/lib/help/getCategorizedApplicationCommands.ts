import { container } from "@sapphire/framework"
import { ApplicationCommandType, Collection, Snowflake } from "discord.js"
import type { CommandHelpData } from "./CommandHelpData"
import { getArgumentsFromOptionsList } from "./getArgumentsFromOptionsList"
import { getSubcommandsFromOptionsList } from "./getSubcommandsFromOptionsList"

const prefixes: Record<ApplicationCommandType, string> = {
  [ApplicationCommandType.ChatInput]: "/",
  [ApplicationCommandType.User]: "(User) ",
  [ApplicationCommandType.Message]: "(Message) ",
}

export const getCategorizedApplicationCommands = () => {
  const entries = container.stores.get("commands").map((command) => {
    if (typeof command.detailedDescription === "string") {
      throw new TypeError(
        `The detailed description of ${command.name} is in an invalid format`,
      )
    }

    const categoryName = command.constructor.name
      .replace(/Command$/, "")
      .replace(/(?!^)[A-Z]/g, (match) => " " + match.toLocaleLowerCase())

    const commands: [Snowflake, CommandHelpData][] = []

    const commandNames = [
      ...command.applicationCommandRegistry.chatInputCommands,
      ...command.applicationCommandRegistry.contextMenuCommands,
    ]

    for (const name of commandNames) {
      const applicationCommand =
        container.client.application?.commands.cache.find(
          (command) => command.name === name,
        )
      if (!applicationCommand) continue

      commands.push([
        applicationCommand.id,
        {
          id: applicationCommand.id,
          displayName:
            prefixes[applicationCommand.type] + applicationCommand.name,
          description:
            applicationCommand.type === ApplicationCommandType.ChatInput
              ? applicationCommand.description
              : command.detailedDescription.contextMenuCommandDescription ?? "",
          arguments: getArgumentsFromOptionsList(applicationCommand.options),
          subcommands: getSubcommandsFromOptionsList(
            applicationCommand.options,
          ),
        },
      ])
    }

    return [categoryName, new Collection(commands)] as const
  })

  return new Collection(entries.filter(([, commands]) => commands.size !== 0))
}
