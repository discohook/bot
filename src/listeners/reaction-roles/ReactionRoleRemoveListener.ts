import { Listener } from "@sapphire/framework"
import {
  DiscordAPIError,
  MessageReaction,
  PartialMessageReaction,
  PartialUser,
  User,
} from "discord.js"
import { getEmojiKey } from "../../lib/emojis/getEmojiKey"
import { getSelf } from "../../lib/guilds/getSelf"
import { getCacheEntry } from "../../lib/storage/getCacheEntry"
import type { ReactionRoleData } from "../../lib/types/ReactionRoleData"

export class ReactionRoleRemoveListener extends Listener {
  public constructor(context: Listener.Context, options: Listener.Options) {
    super(context, {
      ...options,
      name: "reaction-role-remove",
      event: "messageReactionRemove",
    })
  }

  override async run(
    reaction: MessageReaction | PartialMessageReaction,
    user: User | PartialUser,
  ) {
    if (!reaction.message.guild) return

    const self = await getSelf(reaction.message.guild)
    if (!self.permissions.has("MANAGE_ROLES")) return

    const cacheKey = `reaction-role:${reaction.message.id}:${getEmojiKey(
      reaction.emoji,
    )}`
    const roleId = await getCacheEntry(cacheKey, async () => {
      return await this.container
        .database<ReactionRoleData>("reaction_roles")
        .where({
          message_id: reaction.message.id,
          reaction: getEmojiKey(reaction.emoji),
        })
        .first()
        .then((reactionRole) => reactionRole?.role_id ?? "")
    })
    if (!roleId) return

    const role = reaction.message.guild.roles.cache.get(roleId)
    if (!role || !role.editable) return

    try {
      const member = await reaction.message.guild.members.fetch(user.id)
      await member.roles.remove(role)
    } catch (error: unknown) {
      if (error instanceof DiscordAPIError && error.code === 10007) return
      throw error
    }
  }
}
