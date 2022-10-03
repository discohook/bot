import Redis from "ioredis"

export const createCacheConnection = () =>
  new Redis(process.env.CACHE_URL!, {
    keepAlive: 60000 as any,
    reconnectOnError: (error) => error.message.includes("ETIMEDOUT"),
  })
