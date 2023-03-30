import { Listener } from "@sapphire/framework"
import type { GatewayChannelDeleteDispatchData } from "discord.js"
import type { ReactionRoleData } from "../../lib/types/ReactionRoleData"

export class DeleteReactionRoleOnChannelDelete extends Listener {
  public constructor(context: Listener.Context, options: Listener.Options) {
    super(context, {
      ...options,
      name: "delete-reaction-role-on-channel-delete",
      emitter: "ws",
      event: "CHANNEL_DELETE",
    })
  }

  override async run(payload: GatewayChannelDeleteDispatchData) {
    await this.container
      .database<ReactionRoleData>("reaction_roles")
      .where({ channel_id: payload.id })
      .delete()
  }
}
