import {
  InteractionHandler,
  InteractionHandlerTypes,
  PieceContext,
} from "@sapphire/framework"
import type { ButtonInteraction, Snowflake } from "discord.js"
import { fetchAndRestoreMessage } from "../lib/messages/fetchAndRestoreMessage"

type RestoreQuickEditOptions = {
  channelId: Snowflake
  messageId: Snowflake
}

export class RestoreQuickEditHandler extends InteractionHandler {
  constructor(context: PieceContext) {
    super(context, {
      name: "restore-quick-edit",
      interactionHandlerType: InteractionHandlerTypes.Button,
    })
  }

  override async run(
    interaction: ButtonInteraction,
    options: RestoreQuickEditOptions,
  ) {
    await interaction.deferReply({ ephemeral: true })

    fetchAndRestoreMessage(
      interaction,
      options.channelId,
      options.messageId,
      true,
    )
  }

  override async parse(interaction: ButtonInteraction) {
    const match = /^@discohook\/restore-quick-edit\/(\d+)-(\d+)$/.exec(
      interaction.customId,
    )
    if (!match) return this.none()

    return this.some<RestoreQuickEditOptions>({
      channelId: match[1],
      messageId: match[2],
    })
  }
}
