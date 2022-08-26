import { container } from "@sapphire/framework"

export const removeCacheEntry = async (key: string) => {
  await container.cache.del(key)
}
