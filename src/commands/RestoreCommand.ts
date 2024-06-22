import {
  ApplicationCommandRegistry,
  Command,
  type PieceContext,
  RegisterBehavior,
} from "@sapphire/framework"
import {
  ApplicationCommandType,
  ChatInputCommandInteraction,
  ContextMenuCommandBuilder,
  ContextMenuCommandInteraction,
  PermissionFlagsBits,
  SlashCommandBuilder,
} from "discord.js"
import {
  fetchAndRestoreMessage,
  restoreMessageAndReply,
} from "../lib/messages/fetchAndRestoreMessage"
import { parseMessageOption } from "../lib/messages/parseMessageOption"

export class RestoreCommand extends Command {
  constructor(context: PieceContext) {
    super(context, {
      name: "restore",
      detailedDescription: {
        contextMenuCommandDescription:
          "Copies the message's data into the Discohook editor.",
      },
    })
  }

  override async chatInputRun(interaction: ChatInputCommandInteraction) {
    await interaction.deferReply({ ephemeral: true })

    const [channelId, messageId] = await parseMessageOption(interaction)
    if (!channelId || !messageId) return

    fetchAndRestoreMessage(interaction, channelId, messageId, false)
  }

  override async contextMenuRun(interaction: ContextMenuCommandInteraction) {
    if (!interaction.isMessageContextMenuCommand()) return

    await interaction.deferReply({ ephemeral: true })

    await restoreMessageAndReply(interaction, interaction.targetMessage)
  }

  override async registerApplicationCommands(
    registry: ApplicationCommandRegistry,
  ) {
    registry.registerChatInputCommand(
      new SlashCommandBuilder()
        .setName("restore")
        .setDescription(
          "Copies a message's data into the Discohook editor for a given message link.",
        )
        .setDefaultMemberPermissions(PermissionFlagsBits.ManageMessages)
        .addStringOption((option) =>
          option
            .setName("message")
            .setDescription("The message link of the message to restore.")
            .setRequired(true),
        ),
    )

    registry.registerContextMenuCommand(
      new ContextMenuCommandBuilder()
        .setName("Restore to Discohook")
        .setDefaultMemberPermissions(PermissionFlagsBits.ManageMessages)
        .setType(ApplicationCommandType.Message),
      {
        guildIds: process.env.GUILD_ID ? [process.env.GUILD_ID] : undefined,
        behaviorWhenNotIdentical: RegisterBehavior.Overwrite,
      },
    )
  }
}
