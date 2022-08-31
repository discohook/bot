import { ContextMenuCommandBuilder, time } from "@discordjs/builders"
import { fetch } from "@sapphire/fetch"
import {
  ApplicationCommandRegistry,
  Command,
  PieceContext,
  RegisterBehavior,
} from "@sapphire/framework"
import { deepClone } from "@sapphire/utilities"
import {
  ApplicationCommandType,
  PermissionFlagsBits,
} from "discord-api-types/v9"
import { ContextMenuInteraction, MessageEmbed } from "discord.js"

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

  override async contextMenuRun(interaction: ContextMenuInteraction) {
    if (!interaction.isMessageContextMenu()) return

    await interaction.deferReply({ ephemeral: true })

    const embeds = interaction.targetMessage.embeds.map((embed) => {
      if (embed instanceof MessageEmbed) {
        embed = embed.toJSON()
      } else {
        embed = deepClone(embed)
      }

      delete embed.type
      delete embed.video
      delete embed.provider
      for (const image of [embed.image, embed.thumbnail].filter(Boolean)) {
        delete image!.width
        delete image!.height
        delete image!.proxy_url
      }
      for (const image of [embed.footer, embed.author].filter(Boolean)) {
        delete image!.proxy_icon_url
      }

      return embed
    })

    const data = JSON.stringify({
      messages: [
        {
          data: {
            content: interaction.targetMessage.content || undefined,
            embeds: embeds.length === 0 ? undefined : embeds,
          },
        },
      ],
    })
    const encodedData = Buffer.from(data, "utf-8").toString("base64url")
    const url = `https://discohook.app/?data=${encodedData}`

    const response = await fetch<{ url: string; expires: string }>(
      "https://share.discohook.app/create",
      {
        method: "post",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      },
    )

    await interaction.editReply({
      embeds: [
        {
          title: "Restored message",
          description:
            `The restored message can be found at ${response.url}. This link ` +
            `will expire ${time(new Date(response.expires), "R")}.`,
        },
      ],
    })
  }

  override async registerApplicationCommands(
    registry: ApplicationCommandRegistry,
  ) {
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
