import { ContextMenuCommandErrorPayload, Listener } from "@sapphire/framework"
import { ClientApplication, User } from "discord.js"
import { inspect } from "node:util"
import { reply } from "../../lib/interactions/reply"

export class ContextMenuCommandErrorListener extends Listener {
  public constructor(context: Listener.Context) {
    super(context, {
      name: "context-menu-command-error",
      event: "contextMenuCommandError",
    })
  }

  public async run(error: unknown, context: ContextMenuCommandErrorPayload) {
    const application = this.container.client.application as ClientApplication
    if (!application.owner) await application.fetch()

    await reply(context.interaction, {
      content:
        "An unexpected error happened! This has been reported to the " +
        "developers. Try again later.",
    })

    const user =
      application.owner instanceof User
        ? application.owner
        : application.owner?.owner?.user

    await user?.send({
      content: `Encountered error in context menu command ${context.command.name}`,
      files: [
        {
          attachment: Buffer.from(inspect(error), "utf-8"),
          name: "error.js",
        },
      ],
    })
  }
}
