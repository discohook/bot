import type {
  CommandInteraction,
  InteractionReplyOptions,
  MessageComponentInteraction,
} from "discord.js"

export const reply = async (
  interaction: CommandInteraction | MessageComponentInteraction,
  options: InteractionReplyOptions,
  ephemeral = true,
) => {
  if (interaction.replied) {
    await interaction.followUp({ ...options, ephemeral })
  } else if (interaction.deferred) {
    if (ephemeral && !interaction.ephemeral) {
      await interaction.editReply({ content: "\u200b" })
      await interaction.followUp({ ...options, ephemeral })
      return
    }
    await interaction.editReply({ ...options })
  } else {
    await interaction.reply({ ...options, ephemeral })
  }
}
