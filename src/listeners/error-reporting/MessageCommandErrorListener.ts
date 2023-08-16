import { Listener, type MessageCommandErrorPayload } from "@sapphire/framework"
import { ClientApplication, DiscordAPIError, User } from "discord.js"
import { inspect } from "node:util"

export class MessageCommandErrorListener extends Listener {
  public constructor(context: Listener.Context) {
    super(context, {
      name: "message-command-error",
      event: "messageCommandError",
    })
  }

  public async run(error: unknown, context: MessageCommandErrorPayload) {
    if (error instanceof DiscordAPIError && error.code === 10062) return

    const application = this.container.client.application as ClientApplication
    if (!application.owner) await application.fetch()

    const owner =
      application.owner instanceof User
        ? application.owner
        : application.owner?.owner?.user

    await owner?.send({
      content: `Encountered error in message command ${context.command.name}`,
      files: [
        {
          attachment: Buffer.from(inspect(error), "utf-8"),
          name: "error.js",
        },
      ],
    })
  }
}
