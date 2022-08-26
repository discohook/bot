import { Listener, ListenerErrorPayload } from "@sapphire/framework"
import { ClientApplication, User } from "discord.js"
import { inspect } from "node:util"

export class ListenerErrorListener extends Listener {
  public constructor(context: Listener.Context) {
    super(context, {
      name: "listener-error",
      event: "listenerError",
    })
  }

  public async run(error: unknown, context: ListenerErrorPayload) {
    const application = this.container.client.application as ClientApplication
    if (!application.owner) await application.fetch()

    const user =
      application.owner instanceof User
        ? application.owner
        : application.owner?.owner?.user

    await user?.send({
      content: `Encountered error in listener ${context.piece.name}`,
      files: [
        {
          attachment: Buffer.from(inspect(error), "utf-8"),
          name: "error.js",
        },
      ],
    })
  }
}
