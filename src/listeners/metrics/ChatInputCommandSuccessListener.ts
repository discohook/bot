import {
  type ChatInputCommandSuccessPayload,
  Listener,
} from "@sapphire/framework"

export class ChatInputCommandSuccessListener extends Listener {
  public constructor(context: Listener.Context) {
    super(context, {
      name: "chat-input-command-success",
      event: "chatInputCommandSuccess",
    })
  }

  override async run(payload: ChatInputCommandSuccessPayload) {
    const commandName = [
      `/${payload.interaction.commandName}`,
      payload.interaction.options.getSubcommandGroup(false),
      payload.interaction.options.getSubcommand(false),
    ]
      .filter(Boolean)
      .join(" ")

    this.container.metrics.applicationCommandRequestDuration.observe(
      { command: commandName },
      payload.duration / 1000,
    )
  }
}
