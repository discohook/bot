import { container } from "@sapphire/framework"

export const getCacheEntry = async (
  key: string,
  compute: () => string | Promise<string>,
): Promise<string> => {
  let entry = await container.cache.get(key)

  if (entry === null) {
    entry = await compute()
    container.cache.set(key, entry, "EX", 3600)
  }

  return entry
}
