import { ContextMenuCommandSuccessPayload, Listener } from "@sapphire/framework"
import type { ContextMenuInteraction } from "discord.js"

const prefixes: Record<ContextMenuInteraction["targetType"], string> = {
  MESSAGE: "(Message) ",
  USER: "(User) ",
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
          prefixes[payload.interaction.targetType] +
          payload.interaction.commandName,
      },
      payload.duration / 1000,
    )
  }
}
