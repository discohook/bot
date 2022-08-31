import { Listener } from "@sapphire/framework"
import type { GatewayGuildRoleDeleteDispatchData } from "discord-api-types/v9"
import type { ReactionRoleData } from "../../lib/types/ReactionRoleData"

export class DeleteReactionRoleOnGuildRoleDelete extends Listener {
  public constructor(context: Listener.Context, options: Listener.Options) {
    super(context, {
      ...options,
      name: "delete-reaction-role-on-guild-role-delete",
      emitter: "ws",
      event: "GUILD_ROLE_DELETE",
    })
  }

  override async run(payload: GatewayGuildRoleDeleteDispatchData) {
    await this.container
      .database<ReactionRoleData>("reaction_roles")
      .where({ role_id: payload.role_id })
      .delete()
  }
}
