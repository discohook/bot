import {
  type ChatInputCommandDeniedPayload,
  Listener,
  UserError,
} from "@sapphire/framework"

export class ChatInputCommandDeniedListener extends Listener {
  public constructor(context: Listener.Context) {
    super(context, {
      name: "chat-input-command-denied",
      event: "chatInputCommandDenied",
    })
  }

  override async run(error: UserError, payload: ChatInputCommandDeniedPayload) {
    await payload.interaction.reply({
      content: error.message,
      ephemeral: true,
    })
  }
}
