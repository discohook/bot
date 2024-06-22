import {
  type BaseMessageOptions,
  ButtonStyle,
  CommandInteraction,
  ComponentType,
  GuildMember,
  Message,
  MessageComponentInteraction,
  PermissionFlagsBits,
  time,
  ThreadChannel,
  Webhook,
} from "discord.js"
import { getSelf } from "../guilds/getSelf"
import { reply } from "../interactions/reply"
import { fetchWebhooks } from "../webhooks/fetchWebhooks"
import { fetchMessage } from "./fetchMessage"
import { restoreMessage } from "./restoreMessage"

export enum RestoreMode {
  // Just restore the message
  Restore,
  // Require that the message is from a webhook, and include the webhook
  QuickEdit,
  // Act like quick edit if the message is from a webhook, and like restore otherwise
  Open,
}

export const restoreMessageAndReply = async (
  interaction: CommandInteraction | MessageComponentInteraction,
  message: Message,
  mode: RestoreMode = RestoreMode.Restore,
) => {
  let webhook: Webhook | undefined = undefined
  const components: BaseMessageOptions["components"] = []

  if (
    message.webhookId &&
    message.inGuild() &&
    // Check permissions for the bot
    message.channel
      .permissionsFor(await getSelf(message.channel.guild))
      .has(PermissionFlagsBits.ManageWebhooks)
  ) {
    // Now check permissions for the member triggering this
    const member =
      interaction.member instanceof GuildMember
        ? interaction.member
        : await interaction.guild?.members.fetch(interaction.user.id)

    if (
      member &&
      message.channel
        .permissionsFor(member)
        .has(PermissionFlagsBits.ManageWebhooks)
    ) {
      const root =
        message.channel instanceof ThreadChannel
          ? message.channel.parent
          : message.channel
      const webhooks = await fetchWebhooks(root!)

      webhook = webhooks.find((webhook) => webhook.id === message.webhookId)
      if (webhook && mode == RestoreMode.Restore) {
        components.push({
          type: ComponentType.ActionRow,
          components: [
            {
              type: ComponentType.Button,
              style: ButtonStyle.Secondary,
              label: "Quick Edit",
              customId: `@discohook/restore-quick-edit/${message.channelId}-${message.id}`,
            },
          ],
        })
      }
    }
  }

  if (mode == RestoreMode.QuickEdit && !webhook) {
    await reply(interaction, {
      content:
        "I can't find the webhook this message belongs to, therefore " +
        "quick edit is unavailable on this message.",
    })
    return
  }

  if (message.content || message.embeds.length > 0) {
    message = message
  } else if (webhook) {
    message = await webhook.fetchMessage(message.id)
  } else {
    await reply(interaction, {
      content:
        "I can't read the message because of Discord's privacy restrictions. " +
        "To restore this message, right-click or long-press on the message, " +
        "open the apps menu, and select **Restore to Discohook**.",
    })
    return
  }

  const editTarget = mode == RestoreMode.Restore ? undefined : webhook
  const response = await restoreMessage(message, editTarget)

  await reply(interaction, {
    embeds: [
      {
        title: editTarget ? "Opened for editing" : "Restored message",
        description:
          `The message editor can be found at ${response.url}. This link ` +
          `will expire ${time(new Date(response.expires), "R")}.`,
      },
    ],
    components,
  })
}

export const fetchAndRestoreMessage = async (
  interaction: CommandInteraction | MessageComponentInteraction,
  channelId: string,
  messageId: string,
  mode: RestoreMode = RestoreMode.Restore,
) => {
  const message = await fetchMessage(interaction, channelId, messageId)
  if (!message) return

  restoreMessageAndReply(interaction, message, mode)
}
