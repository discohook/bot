import {
  ApplicationCommandRegistry,
  Command,
  type PieceContext,
  RegisterBehavior,
} from "@sapphire/framework"
import {
  type APIMessage,
  ApplicationCommandType,
  type BaseMessageOptions,
  ButtonStyle,
  CategoryChannel,
  ChatInputCommandInteraction,
  ComponentType,
  ContextMenuCommandBuilder,
  ContextMenuCommandInteraction,
  type GuildBasedChannel,
  GuildMember,
  Message,
  PermissionFlagsBits,
  SlashCommandBuilder,
  time,
} from "discord.js"
import { getSelf } from "../lib/guilds/getSelf"
import { fetchAndRestoreMessage } from "../lib/messages/fetchAndRestoreMessage"
import { parseMessageOption } from "../lib/messages/parseMessageOption"
import { restoreMessage } from "../lib/messages/restoreMessage"
import { fetchWebhooks } from "../lib/webhooks/fetchWebhooks"

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

    const response = await restoreMessage(
      interaction.targetMessage as APIMessage | Message,
    )

    const channel = interaction.targetMessage.channel as Exclude<
      GuildBasedChannel,
      CategoryChannel
    >

    const components: BaseMessageOptions["components"] = []
    const webhookId = interaction.targetMessage.webhookId

    if (
      webhookId &&
      interaction.guild &&
      channel
        .permissionsFor(await getSelf(interaction.guild))
        .has(PermissionFlagsBits.ManageWebhooks)
    ) {
      const member =
        interaction.member instanceof GuildMember
          ? interaction.member
          : await interaction.guild.members.fetch(interaction.user.id)

      if (
        channel.permissionsFor(member).has(PermissionFlagsBits.ManageWebhooks)
      ) {
        const webhooks = await fetchWebhooks(channel)

        if (webhooks.some((webhook) => webhook.id === webhookId)) {
          components.push({
            type: ComponentType.ActionRow,
            components: [
              {
                type: ComponentType.Button,
                style: ButtonStyle.Secondary,
                label: "Quick Edit",
                customId: `@discohook/restore-quick-edit/${channel.id}-${interaction.targetId}`,
              },
            ],
          })
        }
      }
    }

    await interaction.editReply({
      embeds: [
        {
          title: "Restored message",
          description:
            `The restored message can be found at ${response.url}. This link ` +
            `will expire ${time(new Date(response.expires), "R")}.`,
        },
      ],
      components,
    })
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
