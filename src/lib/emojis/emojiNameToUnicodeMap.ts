import { emojiData } from "./emojiData"

export const emojiNameToUnicodeMap = Object.fromEntries(
  Object.values(emojiData)
    .flat()
    .flatMap((emoji) => {
      if ("diversityChildren" in emoji) {
        return [
          ...emoji.names.map((name) => [name, emoji.surrogates] as const),
          ...emoji.diversityChildren!.flatMap((diversity) =>
            diversity.names.map(
              (name) => [name, diversity.surrogates] as const,
            ),
          ),
        ]
      }
      return emoji.names.map((name) => [name, emoji.surrogates] as const)
    }),
)
