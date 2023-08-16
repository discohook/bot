import { Precondition, type PieceContext } from "@sapphire/framework"
import { ClientApplication, Message, User } from "discord.js"

export class OwnerOnlyPrecondition extends Precondition {
  constructor(context: PieceContext) {
    super(context, {
      name: "owner-only",
    })
  }

  override async messageRun(message: Message) {
    const application = this.container.client.application as ClientApplication
    if (!application.owner) await application.fetch()

    const allowed =
      application.owner instanceof User
        ? application.owner.id === message.author.id
        : application.owner?.members.has(message.author.id)

    return allowed
      ? this.ok()
      : this.error({ message: "Only the bot owner can use this command." })
  }
}

declare module "@sapphire/framework" {
  interface Preconditions {
    "owner-only": never
  }
}
