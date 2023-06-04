import {
  ApplicationCommandRegistry,
  PieceContext,
  RegisterBehavior,
} from "@sapphire/framework"
import { Subcommand } from "@sapphire/plugin-subcommands"
import {
  ChannelType,
  ChatInputCommandInteraction,
  EmbedBuilder,
  formatEmoji,
  inlineCode,
  SlashCommandBuilder,
} from "discord.js"
import { BOT_EMBED_COLOR } from "../lib/constants"
import { parseEmojiOption } from "../lib/emojis/parseEmojiOption"

export class FormatCommand extends Subcommand {
  constructor(context: PieceContext) {
    super(context, {
      name: "format",
      subcommands: [
        {
          name: "mention",
          chatInputRun: "mentionRun",
        },
        {
          name: "channel",
          chatInputRun: "channelRun",
        },
        {
          name: "emoji",
          chatInputRun: "emojiRun",
        },
      ],
      detailedDescription: {},
    })
  }

  async mentionRun(interaction: ChatInputCommandInteraction) {
    const mentionable = interaction.options.getMentionable("target", true)

    await interaction.reply({
      embeds: [
        new EmbedBuilder()
          .setTitle("Mention")
          .setDescription(inlineCode(String(mentionable)))
          .addFields({ name: "Output", value: String(mentionable) })
          .setColor(BOT_EMBED_COLOR),
      ],
      ephemeral: true,
    })
  }

  async channelRun(interaction: ChatInputCommandInteraction) {
    const channel = interaction.options.getChannel("target", true)

    await interaction.reply({
      embeds: [
        new EmbedBuilder()
          .setTitle("Channel")
          .setDescription(inlineCode(String(channel)))
          .addFields({ name: "Output", value: String(channel) })
          .setColor(BOT_EMBED_COLOR),
      ],
      ephemeral: true,
    })
  }

  async emojiRun(interaction: ChatInputCommandInteraction) {
    const emoji = await parseEmojiOption(interaction, "target")
    if (!emoji) return

    const formatting =
      typeof emoji === "object"
        ? formatEmoji(emoji.id!, emoji.animated ?? false)
        : emoji

    await interaction.reply({
      embeds: [
        new EmbedBuilder()
          .setTitle("Emoji")
          .setDescription(inlineCode(formatting))
          .addFields({ name: "Output", value: formatting })
          .setColor(BOT_EMBED_COLOR),
      ],
      ephemeral: true,
    })
  }

  override async registerApplicationCommands(
    registry: ApplicationCommandRegistry,
  ) {
    registry.registerChatInputCommand(
      new SlashCommandBuilder()
        .setName("format")
        .setDescription("Formatting related commands.")
        .addSubcommand((subcommand) =>
          subcommand
            .setName("mention")
            .setDescription("Gives formatting to mention a given user or role.")
            .addMentionableOption((option) =>
              option
                .setName("target")
                .setDescription("The user or role to show formatting for.")
                .setRequired(true),
            ),
        )
        .addSubcommand((subcommand) =>
          subcommand
            .setName("channel")
            .setDescription("Gives formatting to mention a given channel.")
            .addChannelOption((option) =>
              option
                .setName("target")
                .setDescription("The channel or thread to show formatting for.")
                .addChannelTypes(
                  ChannelType.GuildText,
                  ChannelType.GuildNews,
                  ChannelType.GuildNewsThread,
                  ChannelType.GuildPublicThread,
                  ChannelType.GuildPrivateThread,
                  ChannelType.GuildVoice,
                  ChannelType.GuildStageVoice,
                  ChannelType.GuildForum,
                )
                .setRequired(true),
            ),
        )
        .addSubcommand((subcommand) =>
          subcommand
            .setName("emoji")
            .setDescription("Gives formatting to mention a given emoji.")
            .addStringOption((option) =>
              option
                .setName("target")
                .setDescription("The emoji to show formatting for.")
                .setRequired(true)
                .setAutocomplete(true),
            ),
        ),
      {
        guildIds: process.env.GUILD_ID ? [process.env.GUILD_ID] : undefined,
        behaviorWhenNotIdentical: RegisterBehavior.Overwrite,
      },
    )
  }
}
