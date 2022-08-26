import { emojiData } from "./emojiData"

export const emojiUnicodeToNameMap = Object.fromEntries(
  Object.values(emojiData)
    .flat()
    .flatMap((emoji) => {
      if ("diversityChildren" in emoji) {
        return [
          [emoji.surrogates, emoji.names] as const,
          ...emoji.diversityChildren!.map(
            (diversity) => [diversity.surrogates, diversity.names] as const,
          ),
        ]
      }
      return [[emoji.surrogates, emoji.names]] as const
    }),
)
