import {
  bold,
  channelMention,
  inlineCode,
  SlashCommandBuilder,
  time,
  userMention,
} from "@discordjs/builders"
import { PaginatedMessageEmbedFields } from "@sapphire/discord.js-utilities"
import {
  ApplicationCommandRegistry,
  PieceContext,
  RegisterBehavior,
} from "@sapphire/framework"
import { Subcommand } from "@sapphire/plugin-subcommands"
import { ChannelType, PermissionFlagsBits } from "discord-api-types/v9"
import {
  BaseGuildTextChannel,
  CommandInteraction,
  GuildMember,
  MessageEmbed,
  Webhook,
} from "discord.js"
import {
  BOT_EMBED_COLOR,
  DEFAULT_AVATAR_URL,
  IMAGE_CONTENT_TYPES,
} from "../lib/constants"
import { fetchWebhooks } from "../lib/webhooks/fetchWebhooks"
import { parseWebhookOption } from "../lib/webhooks/parseWebhookOption"

export class WebhookCommand extends Subcommand {
  constructor(context: PieceContext) {
    super(context, {
      name: "webhook",
      runIn: ["GUILD_ANY"],
      requiredUserPermissions: PermissionFlagsBits.ManageWebhooks,
      subcommands: [
        {
          name: "list",
          chatInputRun: "listRun",
        },
        {
          name: "info",
          chatInputRun: "infoRun",
        },
        {
          name: "create",
          chatInputRun: "createRun",
        },
        {
          name: "edit",
          chatInputRun: "editRun",
        },
        {
          name: "delete",
          chatInputRun: "deleteRun",
        },
      ],
      detailedDescription: {},
    })
  }

  async #runAssertions(
    interaction: CommandInteraction,
    channelOption = "channel",
  ) {
    const channel = interaction.options.getChannel(
      channelOption,
    ) as BaseGuildTextChannel | null

    const location = channel ? channelMention(channel.id) : "this server"

    const selfPermissions = channel
      ? interaction.guild!.me!.permissionsIn(channel.id)
      : interaction.guild!.me!.permissions

    if (!selfPermissions.has("MANAGE_WEBHOOKS")) {
      await interaction.editReply({
        content: `I don't have permissions to manage webhooks in ${location}.`,
      })
      return false
    }

    let member = interaction.member
    if (!(member instanceof GuildMember)) {
      member = await interaction.guild!.members.fetch(interaction.user.id)
    }

    const memberPermissions = channel
      ? member.permissionsIn(channel.id)
      : member.permissions

    if (!memberPermissions.has("MANAGE_WEBHOOKS")) {
      await interaction.editReply({
        content: `You don't have permissions to manage webhooks in ${location}.`,
      })
      return false
    }

    return true
  }

  async #replyWithWebhookInfo(
    interaction: CommandInteraction,
    webhook: Webhook,
  ) {
    await interaction.editReply({
      embeds: [
        new MessageEmbed()
          .setTitle(webhook.name)
          .setColor(BOT_EMBED_COLOR)
          .setThumbnail(webhook.avatarURL() ?? DEFAULT_AVATAR_URL)
          .addFields(
            {
              name: "Channel",
              value: channelMention(webhook.channelId),
            },
            {
              name: "Created at",
              value: time(webhook.createdAt),
            },
            {
              name: "Created by",
              value: webhook.owner ? userMention(webhook.owner.id) : "Unknown",
            },
            {
              name: "Webhook URL",
              value: webhook.url,
            },
          ),
      ],
    })
  }

  async listRun(interaction: CommandInteraction) {
    await interaction.deferReply({ ephemeral: true })
    if (!(await this.#runAssertions(interaction))) return

    const channel = interaction.options.getChannel(
      "channel",
    ) as BaseGuildTextChannel | null
    const showIds = interaction.options.getBoolean("show-ids")

    const webhooks = await fetchWebhooks(channel ?? interaction.guild!)

    if (webhooks.length === 0) {
      await interaction.editReply({
        embeds: [
          new MessageEmbed()
            .setTitle("Webhooks")
            .setDescription(
              `It seems like you don't have any webhooks yet. Use ` +
                `${bold("/webhook create")} to create one.`,
            )
            .setColor(BOT_EMBED_COLOR),
        ],
      })
      return
    }

    await new PaginatedMessageEmbedFields()
      .setTemplate(
        new MessageEmbed()
          .setTitle("Webhooks")
          .setDescription(
            `Use ${bold("/webhook info")} to get details on any webhook.`,
          )
          .setColor(BOT_EMBED_COLOR),
      )
      .setItems(
        webhooks.map((webhook, _index, array) => {
          let value = `Channel: ${channelMention(webhook.channelId)}`

          const duplicate = array.some(
            (other) =>
              other.id !== webhook.id &&
              other.name === webhook.name &&
              other.channelId === webhook.channelId,
          )

          if (duplicate || showIds) {
            value += `\nID: ${inlineCode(webhook.id)}`
          }

          return { name: webhook.name, value }
        }),
      )
      .setItemsPerPage(8)
      .make()
      .run(interaction)
  }

  async infoRun(interaction: CommandInteraction) {
    await interaction.deferReply({ ephemeral: true })
    if (!(await this.#runAssertions(interaction))) return

    const webhook = await parseWebhookOption(interaction)
    if (!webhook) return

    await this.#replyWithWebhookInfo(interaction, webhook)
  }

  async createRun(interaction: CommandInteraction) {
    await interaction.deferReply({ ephemeral: true })
    if (!(await this.#runAssertions(interaction))) return

    const channel = interaction.options.getChannel(
      "channel",
      true,
    ) as BaseGuildTextChannel
    const name = interaction.options.getString("name", true)

    if (name.length > 80) {
      await interaction.editReply({
        content: "Webhook names can't be longer than 80 characters.",
      })
      return
    }

    const avatar = interaction.options.getAttachment("avatar")
    if (avatar) {
      if (!IMAGE_CONTENT_TYPES.includes(avatar.contentType ?? "")) {
        await interaction.editReply({
          content: "The avatar given isn't of a supported file type.",
        })
        return
      }
    }

    const webhook = await channel.createWebhook(name, {
      avatar: avatar?.url,
      reason: `Action on behalf of ${interaction.user.tag} (ID: ${interaction.user.id})`,
    })

    await this.#replyWithWebhookInfo(interaction, webhook)
  }

  async editRun(interaction: CommandInteraction) {
    await interaction.deferReply({ ephemeral: true })
    if (!(await this.#runAssertions(interaction))) return

    if (!(await this.#runAssertions(interaction, "move-to"))) return

    let webhook = await parseWebhookOption(interaction)
    if (!webhook) return

    const renameTo = interaction.options.getString("rename-to")
    const moveTo = interaction.options.getChannel("move-to")
    const changeAvatarTo = interaction.options.getAttachment("change-avatar-to")

    if (renameTo && renameTo.length > 80) {
      await interaction.editReply({
        content: "Webhook names can't be longer than 80 characters.",
      })
      return
    }

    if (changeAvatarTo) {
      if (!IMAGE_CONTENT_TYPES.includes(changeAvatarTo.contentType ?? "")) {
        await interaction.editReply({
          content: "The avatar given isn't of a supported file type.",
        })
        return
      }
    }

    webhook = await webhook.edit(
      {
        name: renameTo ?? webhook.name,
        channel: moveTo?.id ?? webhook.channelId,
        avatar: changeAvatarTo?.url,
      },
      `Action on behalf of ${interaction.user.tag} (ID: ${interaction.user.id})`,
    )

    await this.#replyWithWebhookInfo(interaction, webhook)
  }

  async deleteRun(interaction: CommandInteraction) {
    await interaction.deferReply({ ephemeral: true })
    if (!(await this.#runAssertions(interaction))) return

    const webhook = await parseWebhookOption(interaction)
    if (!webhook) return

    await webhook.delete(
      `Action on behalf of ${interaction.user.tag} (ID: ${interaction.user.id})`,
    )

    await interaction.editReply({
      content: `Webhook ${bold(webhook.name)} successfully deleted.`,
    })
  }

  override async registerApplicationCommands(
    registry: ApplicationCommandRegistry,
  ) {
    registry.registerChatInputCommand(
      new SlashCommandBuilder()
        .setName("webhook")
        .setDescription("Webhook management commands.")
        .setDefaultMemberPermissions(PermissionFlagsBits.ManageWebhooks)
        .setDMPermission(false)
        .addSubcommand((subcommand) =>
          subcommand
            .setName("list")
            .setDescription("List existing webhooks in the server.")
            .addChannelOption((option) =>
              option
                .setName("channel")
                .setDescription(
                  "Channel to limit list to, if unset will list webhooks for all channels.",
                )
                .addChannelTypes(ChannelType.GuildText, ChannelType.GuildNews)
                .setRequired(false),
            )
            .addBooleanOption((option) =>
              option
                .setName("show-ids")
                .setDescription("Show the IDs belonging to each webhook.")
                .setRequired(false),
            ),
        )
        .addSubcommand((subcommand) =>
          subcommand
            .setName("info")
            .setDescription("Show info for a given webhook.")
            .addStringOption((option) =>
              option
                .setName("webhook")
                .setDescription("The webhook to show info for.")
                .setRequired(true)
                .setAutocomplete(true),
            )
            .addChannelOption((option) =>
              option
                .setName("channel")
                .setDescription("Channel to limit webhook search to.")
                .addChannelTypes(ChannelType.GuildText, ChannelType.GuildNews)
                .setRequired(false),
            ),
        )
        .addSubcommand((subcommand) =>
          subcommand
            .setName("create")
            .setDescription("Create a new webhook.")
            .addChannelOption((option) =>
              option
                .setName("channel")
                .setDescription(
                  "The channel this webhook should send messages to.",
                )
                .addChannelTypes(ChannelType.GuildText, ChannelType.GuildNews)
                .setRequired(true),
            )
            .addStringOption((option) =>
              option
                .setName("name")
                .setDescription("The name to create the webhook with.")
                .setRequired(true),
            )
            .addAttachmentOption((option) =>
              option
                .setName("avatar")
                .setDescription("The avatar to create the webhook with.")
                .setRequired(false),
            ),
        )
        .addSubcommand((subcommand) =>
          subcommand
            .setName("edit")
            .setDescription("Modifies an existing webhook.")
            .addStringOption((option) =>
              option
                .setName("webhook")
                .setDescription("The webhook to modify.")
                .setRequired(true)
                .setAutocomplete(true),
            )
            .addChannelOption((option) =>
              option
                .setName("channel")
                .setDescription("Channel to limit webhook search to.")
                .addChannelTypes(ChannelType.GuildText, ChannelType.GuildNews)
                .setRequired(false),
            )
            .addStringOption((option) =>
              option
                .setName("rename-to")
                .setDescription("The new name of the webhook.")
                .setRequired(false),
            )
            .addChannelOption((option) =>
              option
                .setName("move-to")
                .setDescription("The channel this webhook should be moved to.")
                .addChannelTypes(ChannelType.GuildText, ChannelType.GuildNews)
                .setRequired(false),
            )
            .addAttachmentOption((option) =>
              option
                .setName("change-avatar-to")
                .setDescription("The new avatar of the webhook.")
                .setRequired(false),
            ),
        )
        .addSubcommand((subcommand) =>
          subcommand
            .setName("delete")
            .setDescription("Deletes a given webhook.")
            .addStringOption((option) =>
              option
                .setName("webhook")
                .setDescription("Webhook to delete.")
                .setRequired(true)
                .setAutocomplete(true),
            )
            .addChannelOption((option) =>
              option
                .setName("channel")
                .setDescription("Channel to limit webhook search to.")
                .addChannelTypes(ChannelType.GuildText, ChannelType.GuildNews)
                .setRequired(false),
            ),
        ),
      {
        guildIds: process.env.GUILD_ID ? [process.env.GUILD_ID] : undefined,
        behaviorWhenNotIdentical: RegisterBehavior.Overwrite,
      },
    )
  }
}
