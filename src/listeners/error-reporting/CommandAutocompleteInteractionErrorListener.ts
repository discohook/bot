import { DiscordAPIError as RestDiscordAPIError } from "@discordjs/rest"
import { AutocompleteInteractionPayload, Listener } from "@sapphire/framework"
import { ClientApplication, DiscordAPIError, User } from "discord.js"
import { inspect } from "node:util"

export class CommandAutocompleteInteractionErrorListener extends Listener {
  public constructor(context: Listener.Context) {
    super(context, {
      name: "command-autocomplete-interaction-error",
      event: "CommandAutocompleteInteractionError",
    })
  }

  public async run(error: unknown, context: AutocompleteInteractionPayload) {
    const application = this.container.client.application as ClientApplication
    if (!application.owner) await application.fetch()

    if (
      (error instanceof DiscordAPIError ||
        error instanceof RestDiscordAPIError) &&
      error.code === 10062
    ) {
      return
    }

    const user =
      application.owner instanceof User
        ? application.owner
        : application.owner?.owner?.user

    await user?.send({
      content: `Encountered error in command autocomplete interaction ${context.command.name}`,
      files: [
        {
          attachment: Buffer.from(inspect(error), "utf-8"),
          name: "error.js",
        },
      ],
    })
  }
}
