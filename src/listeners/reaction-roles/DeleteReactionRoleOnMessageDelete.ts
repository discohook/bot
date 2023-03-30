import { Listener } from "@sapphire/framework"
import type { GatewayMessageDeleteDispatchData } from "discord.js"
import type { ReactionRoleData } from "../../lib/types/ReactionRoleData"

export class DeleteReactionRoleOnMessageDelete extends Listener {
  public constructor(context: Listener.Context, options: Listener.Options) {
    super(context, {
      ...options,
      name: "delete-reaction-role-on-message-delete",
      emitter: "ws",
      event: "MESSAGE_DELETE",
    })
  }

  override async run(payload: GatewayMessageDeleteDispatchData) {
    await this.container
      .database<ReactionRoleData>("reaction_roles")
      .where({ message_id: payload.id })
      .delete()
  }
}
