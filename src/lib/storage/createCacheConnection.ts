import Redis from "ioredis"

export const createCacheConnection = () => new Redis(process.env.CACHE_URL!)
