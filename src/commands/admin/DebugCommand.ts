import { Command, PieceContext } from "@sapphire/framework"
import type { Message } from "discord.js"

export class DebugCommand extends Command {
  constructor(context: PieceContext) {
    super(context, {
      name: "debug",
      quotes: [],
      detailedDescription: {},
    })
  }

  override async messageRun(message: Message) {
    const shard = message.guild?.shard ?? this.container.client.ws.shards.get(0)

    return message.reply({
      content:
        "```" +
        `\nGuild: ${message.guild?.id ?? "N/A"}` +
        `\nShard: ${shard?.id}` +
        `\nPing:  ${shard?.ping}` +
        "\n```",
    })
  }
}
