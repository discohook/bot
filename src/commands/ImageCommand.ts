import { SlashCommandBuilder } from "@discordjs/builders"
import { CDN } from "@discordjs/rest"
import {
  ApplicationCommandRegistry,
  PieceContext,
  RegisterBehavior,
} from "@sapphire/framework"
import { Subcommand } from "@sapphire/plugin-subcommands"
import { CommandInteraction, MessageEmbed } from "discord.js"
import { BOT_EMBED_COLOR } from "../lib/constants"
import { parseEmojiOption } from "../lib/emojis/parseEmojiOption"

export class ImageCommand extends Subcommand {
  constructor(context: PieceContext) {
    super(context, {
      name: "image",
      subcommands: [
        {
          name: "avatar",
          chatInputRun: "avatarRun",
        },
        {
          name: "icon",
          chatInputRun: "iconRun",
        },
        {
          name: "emoji",
          chatInputRun: "emojiRun",
        },
      ],
      detailedDescription: {},
    })
  }

  async avatarRun(interaction: CommandInteraction) {
    const user = interaction.options.getUser("user", true)
    const member = interaction.options.getMember("user")

    const dynamic = !(interaction.options.getBoolean("static") ?? false)
    const avatar = user.displayAvatarURL({ format: "png", dynamic })

    const embed = new MessageEmbed()
      .setTitle(`Avatar for ${user.tag}`)
      .setDescription(avatar)
      .setImage(avatar)
      .setColor(BOT_EMBED_COLOR)

    if (member?.avatar) {
      const memberAvatar = new CDN().guildMemberAvatar(
        interaction.guild!.id,
        user.id,
        member.avatar,
        { extension: "png", forceStatic: !dynamic },
      )

      embed
        .addFields({ name: "Server Avatar", value: memberAvatar })
        .setImage(memberAvatar)
        .setThumbnail(avatar)
    }

    await interaction.reply({
      embeds: [embed],
      ephemeral: true,
    })
  }

  async iconRun(interaction: CommandInteraction) {
    if (!interaction.guild) {
      await interaction.reply({
        content: "This command can only be run in a server.",
        ephemeral: true,
      })
      return
    }

    const dynamic = !(interaction.options.getBoolean("static") ?? false)
    const url = interaction.guild.iconURL({ format: "png", dynamic })

    if (!url) {
      await interaction.reply({
        content: "This server does not have an icon.",
        ephemeral: true,
      })
      return
    }

    await interaction.reply({
      embeds: [
        new MessageEmbed()
          .setTitle(`Server icon for ${interaction.guild.name}`)
          .setDescription(url)
          .setImage(url)
          .setColor(BOT_EMBED_COLOR),
      ],
      ephemeral: true,
    })
  }

  async emojiRun(interaction: CommandInteraction) {
    const emoji = await parseEmojiOption(interaction, "target")
    if (!emoji) return

    const dynamic = !(interaction.options.getBoolean("static") ?? false)

    const name = typeof emoji === "object" ? `:${emoji.name}:` : emoji

    const url =
      typeof emoji === "object"
        ? new CDN().emoji(emoji.id!, emoji.animated && dynamic ? "gif" : "png")
        : "https://twemoji.maxcdn.com/v/13.1.0/72x72/" +
          [...emoji]
            .map((character) => character.codePointAt(0)?.toString(16))
            .join("-") +
          ".png"

    const embed = new MessageEmbed()
      .setTitle(`Emoji image for ${name}`)
      .setDescription(url)
      .setImage(url)

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
        .setName("image")
        .setDescription("Utility to grab image URLs from Discord.")
        .addSubcommand((subcommand) =>
          subcommand
            .setName("avatar")
            .setDescription("Gives the avatar URL of a Discord user.")
            .addUserOption((option) =>
              option
                .setName("user")
                .setDescription("The user to get their avatar URL from.")
                .setRequired(true),
            )
            .addBooleanOption((option) =>
              option
                .setName("static")
                .setDescription("If animated avatars should be ignored.")
                .setRequired(false),
            ),
        )
        .addSubcommand((subcommand) =>
          subcommand
            .setName("icon")
            .setDescription("Gives the icon URL of this Discord server.")
            .addBooleanOption((option) =>
              option
                .setName("static")
                .setDescription("If animated icons should be ignored.")
                .setRequired(false),
            ),
        )
        .addSubcommand((subcommand) =>
          subcommand
            .setName("emoji")
            .setDescription("Gives the image URL of a Discord emoji.")
            .addStringOption((option) =>
              option
                .setName("target")
                .setDescription("The emoji to get its image URL from.")
                .setRequired(true)
                .setAutocomplete(true),
            )
            .addBooleanOption((option) =>
              option
                .setName("static")
                .setDescription("If animated emojis should be ignored.")
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
