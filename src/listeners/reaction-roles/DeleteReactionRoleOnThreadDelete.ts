import { Listener } from "@sapphire/framework"
import type { GatewayThreadDeleteDispatchData } from "discord-api-types/v9"
import type { ReactionRoleData } from "../../lib/types/ReactionRoleData"

export class DeleteReactionRoleOnThreadDelete extends Listener {
  public constructor(context: Listener.Context, options: Listener.Options) {
    super(context, {
      ...options,
      name: "delete-reaction-role-on-thread-delete",
      emitter: "ws",
      event: "THREAD_DELETE",
    })
  }

  override async run(payload: GatewayThreadDeleteDispatchData) {
    await this.container
      .database<ReactionRoleData>("reaction_roles")
      .where({ channel_id: payload.id })
      .delete()
  }
}
