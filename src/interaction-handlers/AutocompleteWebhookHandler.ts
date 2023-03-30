import { AutoCompleteLimits } from "@sapphire/discord-utilities"
import {
  InteractionHandler,
  InteractionHandlerTypes,
  PieceContext,
} from "@sapphire/framework"
import {
  ApplicationCommandOptionType,
  AutocompleteInteraction,
  BaseGuildTextChannel,
  CategoryChannel,
  Guild,
  GuildBasedChannel,
} from "discord.js"
import { ellipsize } from "../lib/lang/ellipsize"
import { fetchWebhooks } from "../lib/webhooks/fetchWebhooks"

type AutocompleteWebhookOptions = {
  source: Guild | Exclude<GuildBasedChannel, CategoryChannel>
  query: string
}

export class AutocompleteWebhookHandler extends InteractionHandler {
  constructor(context: PieceContext) {
    super(context, {
      name: "autocomplete-webhook",
      interactionHandlerType: InteractionHandlerTypes.Autocomplete,
    })
  }

  override async run(
    interaction: AutocompleteInteraction,
    options: AutocompleteWebhookOptions,
  ) {
    const guild = interaction.guild as Guild
    const webhooks = await fetchWebhooks(options.source)

    await interaction.respond(
      webhooks
        .filter((webhook) => {
          const channel =
            options.source instanceof BaseGuildTextChannel
              ? options.source
              : guild.channels.cache.get(webhook.channelId)!
          const words = options.query.toLocaleLowerCase().split(/\s+/)

          if (words.includes(channel.id) || words.includes(webhook.id)) {
            return true
          }

          return [
            ...webhook.name.toLocaleLowerCase().split(/\s+/),
            ...channel.name.toLocaleLowerCase().split(/\s+/),
          ].some((word) => words.some((query) => word.includes(query)))
        })
        .slice(0, AutoCompleteLimits.MaximumAmountOfOptions)
        .map((webhook) => {
          let name = ""

          if (options.source instanceof Guild) {
            const channel = guild.channels.cache.get(webhook.channelId)!
            name += `#${channel.name}: `
          }

          name += webhook.name

          return {
            name: ellipsize(
              name,
              AutoCompleteLimits.MaximumLengthOfNameOfOption,
            ),
            value: webhook.id,
          }
        }),
    )
  }

  override async parse(interaction: AutocompleteInteraction) {
    if (!interaction.inGuild()) return this.none()

    const { name, value } = interaction.options.getFocused(true)
    if (name !== "webhook") return this.none()

    let source: Guild | Guild | Exclude<GuildBasedChannel, CategoryChannel> =
      interaction.guild!

    // Using options.get("channel") as Discord doesn't give channel data in
    // autocomplete interactions which trips up the resolver
    const channelOption = interaction.options.get("channel")
    if (channelOption?.type === ApplicationCommandOptionType.Channel) {
      const channel = interaction.guild!.channels.cache.get(
        String(channelOption.value),
      )

      if (channel instanceof BaseGuildTextChannel) source = channel
    }

    return this.some<AutocompleteWebhookOptions>({
      source,
      query: String(value),
    })
  }
}
