import { ContextMenuCommandSuccessPayload, Listener } from "@sapphire/framework"
import { APIContextMenuInteraction, ApplicationCommandType } from "discord.js"

const prefixes: Record<APIContextMenuInteraction["data"]["type"], string> = {
  [ApplicationCommandType.Message]: "(Message) ",
  [ApplicationCommandType.User]: "(User) ",
}

export class ContextMenuCommandSuccessListener extends Listener {
  public constructor(context: Listener.Context) {
    super(context, {
      name: "context-menu-command-success",
      event: "contextMenuCommandSuccess",
    })
  }

  override async run(payload: ContextMenuCommandSuccessPayload) {
    this.container.metrics.applicationCommandRequestDuration.observe(
      {
        command:
          prefixes[payload.interaction.commandType] +
          payload.interaction.commandName,
      },
      payload.duration / 1000,
    )
  }
}
