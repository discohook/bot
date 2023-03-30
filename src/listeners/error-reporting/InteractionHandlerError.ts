import { InteractionHandlerError, Listener } from "@sapphire/framework"
import { ClientApplication, DiscordAPIError, User } from "discord.js"
import { inspect } from "node:util"
import { reply } from "../../lib/interactions/reply"

export class InteractionHandlerErrorListener extends Listener {
  public constructor(context: Listener.Context) {
    super(context, {
      name: "interaction-handler-error",
      event: "interactionHandlerError",
    })
  }

  public async run(error: unknown, context: InteractionHandlerError) {
    if (error instanceof DiscordAPIError && error.code === 10062) return

    if (
      context.interaction.isCommand() ||
      context.interaction.isMessageComponent()
    ) {
      await reply(context.interaction, {
        content:
          "An unexpected error happened! This has been reported to the " +
          "developers. Try again later.",
      })
    }

    const application = this.container.client.application as ClientApplication
    if (!application.owner) await application.fetch()

    const owner =
      application.owner instanceof User
        ? application.owner
        : application.owner?.owner?.user

    await owner?.send({
      content: `Encountered error in interaction handler ${context.handler.name}`,
      files: [
        {
          attachment: Buffer.from(inspect(error), "utf-8"),
          name: "error.js",
        },
      ],
    })
  }
}
