import { URL } from 'node:url'
import { fetch } from "@sapphire/fetch"
import { ThreadChannel, Message, Webhook } from "discord.js"

export const restoreMessage = async (message: Message, target?: Webhook) => {
  const embeds = message.embeds.map((embedObject) => {
    const embed = embedObject.toJSON()

    delete embed.type
    delete embed.video
    delete embed.provider
    for (const image of [embed.image, embed.thumbnail].filter(Boolean)) {
      delete image!.width
      delete image!.height
      delete image!.proxy_url
    }
    for (const image of [embed.footer, embed.author].filter(Boolean)) {
      delete image!.proxy_icon_url
    }

    return embed
  })

  let webhookUrl = target?.url
  if (webhookUrl && message.channel instanceof ThreadChannel) {
    let newUrl = new URL(webhookUrl)
    newUrl.searchParams.set("thread_id", message.channel.id)
    webhookUrl = newUrl.toString()
  }

  const data = JSON.stringify({
    messages: [
      {
        data: {
          content: message.content || undefined,
          embeds: embeds.length === 0 ? undefined : embeds,
        },
        reference: target ? message.url : undefined,
      },
    ],
    targets: [{ url: webhookUrl }],
  })
  const encodedData = Buffer.from(data, "utf-8").toString("base64url")
  const url = `https://discohook.app/?data=${encodedData}`

  const response = await fetch<{ url: string; expires: string }>(
    "https://share.discohook.app/create",
    {
      method: "post",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    },
  )

  return response
}
