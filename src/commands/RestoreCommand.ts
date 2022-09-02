import {
  ContextMenuCommandBuilder,
  SlashCommandBuilder,
  time,
} from "@discordjs/builders"
import {
  ApplicationCommandRegistry,
  Command,
  PieceContext,
  RegisterBehavior,
} from "@sapphire/framework"
import type { APIMessage } from "discord-api-types/v10"
import {
  ApplicationCommandType,
  PermissionFlagsBits,
} from "discord-api-types/v9"
import {
  AnyChannel,
  CommandInteraction,
  ContextMenuInteraction,
  GuildChannel,
  GuildMember,
  Message,
  MessageOptions,
  TextBasedChannel,
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

  override async chatInputRun(interaction: CommandInteraction) {
    await interaction.deferReply({ ephemeral: true })

    const [channelId, messageId] = await parseMessageOption(interaction)
    if (!channelId || !messageId) return

    fetchAndRestoreMessage(interaction, channelId, messageId, false)
  }

  override async contextMenuRun(interaction: ContextMenuInteraction) {
    if (!interaction.isMessageContextMenu()) return

    await interaction.deferReply({ ephemeral: true })

    const response = await restoreMessage(
      interaction.targetMessage as APIMessage | Message,
    )

    const channel = (
      interaction.targetMessage instanceof Message
        ? interaction.targetMessage.channel
        : interaction.guild?.channels.cache.get(
            interaction.targetMessage.channel_id,
          )
    ) as Extract<Extract<AnyChannel, TextBasedChannel>, GuildChannel>

    const components: MessageOptions["components"] = []
    const webhookId =
      interaction.targetMessage instanceof Message
        ? interaction.targetMessage.webhookId
        : interaction.targetMessage.webhook_id

    if (
      webhookId &&
      interaction.guild &&
      channel
        .permissionsFor(await getSelf(interaction.guild))
        .has("MANAGE_WEBHOOKS")
    ) {
      const member =
        interaction.member instanceof GuildMember
          ? interaction.member
          : await interaction.guild.members.fetch(interaction.user.id)

      if (channel.permissionsFor(member).has("MANAGE_WEBHOOKS")) {
        const webhooks = await fetchWebhooks(channel)

        if (webhooks.some((webhook) => webhook.id === webhookId)) {
          components.push({
            type: "ACTION_ROW",
            components: [
              {
                type: "BUTTON",
                style: "SECONDARY",
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
