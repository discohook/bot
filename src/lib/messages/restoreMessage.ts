import { fetch } from "@sapphire/fetch"
import { deepClone } from "@sapphire/utilities"
import { type APIMessage, Embed, Message, Webhook } from "discord.js"

export const restoreMessage = async (
  message: APIMessage | Message,
  target?: Webhook,
) => {
  const embeds = message.embeds.map((embed) => {
    if (embed instanceof Embed) {
      embed = embed.toJSON()
    } else {
      embed = deepClone(embed)
    }

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

  const data = JSON.stringify({
    messages: [
      {
        data: {
          content: message.content || undefined,
          embeds: embeds.length === 0 ? undefined : embeds,
        },
        reference: target
          ? message instanceof Message
            ? message.url
            : message.id
          : undefined,
      },
    ],
    targets: target ? [{ url: target.url }] : undefined,
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
