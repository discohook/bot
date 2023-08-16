import {
  ApplicationCommandRegistry,
  Command,
  type PieceContext,
  RegisterBehavior,
} from "@sapphire/framework"
import {
  type APIEmbedField,
  ChatInputCommandInteraction,
  CommandInteraction,
  EmbedBuilder,
  SlashCommandBuilder,
} from "discord.js"
import { BOT_EMBED_COLOR } from "../lib/constants"
import { getCategorizedApplicationCommands } from "../lib/help/getCategorizedApplicationCommands"
import { parseApplicationCommandOption } from "../lib/help/parseApplicationCommandOption"
import { stringifyCommand } from "../lib/help/stringifyCommand"

export class HelpCommand extends Command {
  constructor(context: PieceContext) {
    super(context, {
      name: "help",
      detailedDescription: {},
    })
  }

  override async chatInputRun(interaction: ChatInputCommandInteraction) {
    if (!interaction.options.get("command")) {
      await this.#default(interaction)
      return
    }

    this.#commandInfo(interaction)
  }

  async #default(interaction: CommandInteraction) {
    await interaction.reply({
      embeds: [
        new EmbedBuilder()
          .setTitle("Help")
          .setDescription(
            [
              "Hey, this is Discohook's official helper bot. I am here to make " +
                "things easier on you and to power certain features within Discohook.",
              "If you need help, feel free to join the community at <https://discohook.app/discord>, " +
                "you'll find channels dedicated to asking questions there.",
              "You can view the site at <https://discohook.app/>, and you can " +
                "invite me using <https://discohook.app/bot>.",
              "A list of commands this bot provides is below, use **/help [command]** " +
                " for more info on how to use any given command.",
            ].join("\n\n"),
          )
          .addFields(
            getCategorizedApplicationCommands().map(
              (commands, name): APIEmbedField => ({
                name,
                value: commands
                  .map((command) =>
                    stringifyCommand(command, { includeSubCommands: true }),
                  )
                  .join("\n"),
              }),
            ),
          )
          .setColor(BOT_EMBED_COLOR),
      ],
      ephemeral: true,
    })
  }

  async #commandInfo(interaction: ChatInputCommandInteraction) {
    const result = await parseApplicationCommandOption(interaction)
    if (!result) return

    const [command, subcommandName] = result

    const displayName = (command.displayName + " " + subcommandName).trim()

    const { description, arguments: commandArguments } = subcommandName
      ? command.subcommands.find(
          (subcommand) => subcommand.name === subcommandName,
        )!
      : command

    const embed = new EmbedBuilder()
      .setTitle(`Command help: ${displayName}`)
      .setDescription(description)
      .setColor(BOT_EMBED_COLOR)

    if (!subcommandName) {
      embed.addFields(
        ...command.subcommands.map((subcommand) => ({
          name: `${subcommand.name} - Subcommand`,
          value: subcommand.description,
        })),
      )
    }

    embed.addFields(
      ...commandArguments.map((option) => ({
        name: `${option.name} - ${option.required ? "Required" : "Optional"}`,
        value: option.description,
      })),
    )

    await interaction.reply({
      embeds: [embed],
      ephemeral: true,
    })
  }

  override async registerApplicationCommands(
    registry: ApplicationCommandRegistry,
  ) {
    registry.registerChatInputCommand(
      new SlashCommandBuilder()
        .setName("help")
        .setDescription("Get help on how to use this bot.")
        .addStringOption((option) =>
          option
            .setName("command")
            .setDescription("Command to provide details for.")
            .setRequired(false)
            .setAutocomplete(true),
        ),
      {
        guildIds: process.env.GUILD_ID ? [process.env.GUILD_ID] : undefined,
        behaviorWhenNotIdentical: RegisterBehavior.Overwrite,
      },
    )
  }
}
