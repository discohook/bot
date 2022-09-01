import { container, LogLevel, SapphireClient } from "@sapphire/framework"
import "@sapphire/plugin-api/register"
import "@sapphire/plugin-logger/register"
import { GatewayIntentBits } from "discord-api-types/v9"
import {
  ClientOptions,
  GuildMember,
  Options,
  ThreadMember,
  User,
} from "discord.js"
import { config } from "dotenv-cra"
import type { Redis } from "ioredis"
import type { Knex } from "knex"
import "reflect-metadata"
import { Metrics } from "./lib/metrics/Metrics"
import { createCacheConnection } from "./lib/storage/createCacheConnection"
import { createDatabaseConnection } from "./lib/storage/createDatabaseConnection"

process.env.NODE_ENV ??= "development"
config()

let shardConfig: Pick<ClientOptions, "shards" | "shardCount"> = {
  shards: "auto",
}

if (process.env.SHARD_COUNT) {
  const shardCount = Number(process.env.SHARD_COUNT)
  const clusterCount = Number(process.env.CLUSTER_COUNT ?? 1)
  const clusterSize = shardCount / clusterCount
  const cluster = Number(process.env.CLUSTER_ID ?? 0)

  if (shardCount % clusterCount !== 0) {
    console.error(
      `SHARD_COUNT (${shardCount}) is not a multiple of CLUSTER_COUNT (${clusterCount}).`,
    )
    process.exit(1)
  }

  shardConfig = {
    shards: new Array(shardCount)
      .fill(undefined)
      .map((_, index) => index)
      .filter((shard) => Math.floor(shard / clusterSize) === cluster),
    shardCount,
  }
}

const createUserManagerCache = () => {
  return {
    maxSize: 1,
    keepOverLimit: (user: User | GuildMember | ThreadMember) =>
      user.id === user.client.user?.id,
  }
}

const client = new SapphireClient({
  ...shardConfig,
  intents:
    GatewayIntentBits.Guilds |
    GatewayIntentBits.GuildMembers |
    GatewayIntentBits.GuildEmojisAndStickers |
    GatewayIntentBits.GuildMessages |
    GatewayIntentBits.GuildMessageReactions |
    GatewayIntentBits.DirectMessages,
  partials: [
    "CHANNEL",
    "USER",
    "GUILD_MEMBER",
    "MESSAGE",
    "REACTION",
    "GUILD_SCHEDULED_EVENT",
  ],
  makeCache: Options.cacheWithLimits({
    ...Options.defaultMakeCacheSettings,
    UserManager: createUserManagerCache(),
    GuildMemberManager: createUserManagerCache(),
    ReactionUserManager: createUserManagerCache(),
    ThreadMemberManager: createUserManagerCache(),
    MessageManager: 0,
  }),
  sweepers: {
    users: {
      filter: () => (user) => user.id !== user.client.user?.id,
      interval: 900,
    },
    guildMembers: {
      filter: () => (member) => member.id !== member.client.user?.id,
      interval: 900,
    },
  },
  allowedMentions: {
    parse: [],
    repliedUser: false,
  },
  presence: {
    activities: [{ type: "PLAYING", name: "at discohook.app" }],
    status: "online",
  },
  loadMessageCommandListeners: true,
  caseInsensitiveCommands: true,
  logger: {
    level:
      {
        TRACE: LogLevel.Trace,
        DEBUG: LogLevel.Debug,
        INFO: LogLevel.Info,
        WARN: LogLevel.Warn,
        ERROR: LogLevel.Error,
        FATAL: LogLevel.Fatal,
        NONE: LogLevel.None,
      }[String(process.env.LOG_LEVEL)] ?? LogLevel.Info,
  },
  api: {
    listenOptions: {
      host: "0.0.0.0",
      port: Number(process.env.API_PORT) ?? 9100,
    },
  },
})

const main = async () => {
  try {
    container.metrics = new Metrics()

    container.database = createDatabaseConnection()
    container.cache = createCacheConnection()

    client.logger.info("Logging in")
    await client.login(process.env.DISCORD_TOKEN)
  } catch (error) {
    client.logger.fatal(error)
    client.destroy()
    process.exit(1)
  }
}

main()

declare module "@sapphire/pieces" {
  interface Container {
    database: Knex<any, unknown[]>
    cache: Redis
    metrics: Metrics
  }
}
