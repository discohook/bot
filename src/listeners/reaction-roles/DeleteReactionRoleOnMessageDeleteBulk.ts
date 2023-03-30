import { Listener } from "@sapphire/framework"
import type { GatewayMessageDeleteBulkDispatchData } from "discord.js"
import type { ReactionRoleData } from "../../lib/types/ReactionRoleData"

export class DeleteReactionRoleOnMessageDeleteBulk extends Listener {
  public constructor(context: Listener.Context, options: Listener.Options) {
    super(context, {
      ...options,
      name: "delete-reaction-role-on-message-delete-bulk",
      emitter: "ws",
      event: "MESSAGE_DELETE_BULK",
    })
  }

  override async run(payload: GatewayMessageDeleteBulkDispatchData) {
    await this.container
      .database<ReactionRoleData>("reaction_roles")
      .whereIn("message_id", payload.ids)
      .delete()
  }
}
