import { time } from "@discordjs/builders"
import type { APIMessage } from "discord-api-types/v10"
import {
  BaseCommandInteraction,
  GuildMember,
  Message,
  MessageComponentInteraction,
  MessageOptions,
  Permissions,
  ThreadChannel,
  Webhook,
} from "discord.js"
import { getSelf } from "../guilds/getSelf"
import { reply } from "../interactions/reply"
import { fetchWebhooks } from "../webhooks/fetchWebhooks"
import { fetchMessage } from "./fetchMessage"
import { restoreMessage } from "./restoreMessage"

export const fetchAndRestoreMessage = async (
  interaction: BaseCommandInteraction | MessageComponentInteraction,
  channelId: string,
  messageId: string,
  quickEdit = false,
) => {
  const message = await fetchMessage(interaction, channelId, messageId)
  if (!message) return

  const selfPermissions =
    "guild" in message.channel && message.channel.guild
      ? message.channel.permissionsFor(await getSelf(message.channel.guild))
      : new Permissions(Permissions.DEFAULT)

  let webhook: Webhook | undefined = undefined
  const components: MessageOptions["components"] = []
  if (message.webhookId && selfPermissions.has("MANAGE_WEBHOOKS")) {
    const member =
      interaction.member instanceof GuildMember
        ? interaction.member
        : await interaction.guild?.members.fetch(interaction.user.id)

    if (
      member &&
      "guild" in message.channel &&
      message.channel.permissionsFor(member).has("MANAGE_WEBHOOKS")
    ) {
      const root =
        message.channel instanceof ThreadChannel
          ? message.channel.parent
          : message.channel
      const webhooks = await fetchWebhooks(root!)

      webhook = webhooks.find((webhook) => webhook.id === message.webhookId)
      if (webhook && !quickEdit) {
        components.push({
          type: "ACTION_ROW",
          components: [
            {
              type: "BUTTON",
              style: "SECONDARY",
              label: "Quick Edit",
              customId: `@discohook/restore-quick-edit/${channelId}-${messageId}`,
            },
          ],
        })
      }
    }
  }

  if (!webhook && quickEdit) {
    await interaction.editReply({
      content:
        "I can't find the webhook this message belongs to, therefore " +
        "quick edit is unavailable on this message.",
    })
    return
  }

  if (message.content || message.embeds.length > 0) {
    const response = await restoreMessage(
      message,
      quickEdit ? webhook : undefined,
    )
    await reply(interaction, {
      embeds: [
        {
          title: "Restored message",
          description:
            `The restored message can be found at ${response.url}. This link ` +
            `will expire ${time(new Date(response.expires), "R")}.`,
        },
      ],
      components,
    })
    return
  }

  if (!webhook) {
    await reply(interaction, {
      content:
        "I can't read the message because of Discord's privacy restrictions. " +
        "To restore this message, right-click or long-press on the message, " +
        "open the apps menu, and select **Restore to Discohook**.",
    })
    return
  }

  const webhookMessage = await webhook.fetchMessage(messageId)
  const response = await restoreMessage(
    webhookMessage as Message | APIMessage,
    quickEdit ? webhook : undefined,
  )
  await reply(interaction, {
    embeds: [
      {
        title: "Restored message",
        description:
          `The restored message can be found at ${response.url}. This link ` +
          `will expire ${time(new Date(response.expires), "R")}.`,
      },
    ],
    components,
  })
}
