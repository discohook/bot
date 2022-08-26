import { container } from "@sapphire/framework"
import {
  collectDefaultMetrics,
  Counter,
  exponentialBuckets,
  Gauge,
  Histogram,
  Registry,
} from "prom-client"

export class Metrics {
  registry = new Registry()

  shardReady = new Gauge({
    name: "discord_shard_ready",
    help: "Whether the shard was ready while the metrics were being scraped",
    labelNames: ["shard"],
    collect() {
      for (const shard of container.client.ws.shards.values()) {
        this.set({ shard: shard.id }, Number(shard.status === 0))
      }
    },
    registers: [this.registry],
  })

  gatewayDispatchEvents = new Counter({
    name: "discord_gateway_dispatch_events",
    help: "Amount of gateway dispatch events received",
    labelNames: ["event", "shard"] as const,
    registers: [this.registry],
  })

  wsLatency = new Gauge({
    name: "discord_ws_ping_seconds",
    help:
      "Time it takes for Discord to acknowledge heartbeats of the webscoket " +
      "connection in seconds",
    labelNames: ["shard"],
    collect() {
      for (const shard of container.client.ws.shards.values()) {
        if (shard.ping === -1) {
          this.remove({ shard: shard.id })
        } else {
          this.set({ shard: shard.id }, shard.ping / 1000)
        }
      }
    },
    registers: [this.registry],
  })

  applicationCommandRequestDuration = new Histogram({
    name: "discord_application_command_request_duration_seconds",
    help: "Time it takes for an application command to respond in seconds",
    labelNames: ["command"],
    buckets: exponentialBuckets(0.15, 2, 5),
    registers: [this.registry],
  })

  totalGuilds = new Gauge({
    name: "discord_total_guilds",
    help: "Amount of guilds the bot is in",
    labelNames: ["shard"],
    collect() {
      const shards: Record<number, number> = {}

      for (const shard of container.client.ws.shards.values()) {
        shards[shard.id] = 0
      }

      for (const guild of container.client.guilds.cache.values()) {
        shards[guild.shardId]++
      }

      for (const [key, value] of Object.entries(shards)) {
        this.set({ shard: Number(key) }, value)
      }
    },
    registers: [this.registry],
  })

  constructor() {
    this.registry.setDefaultLabels({
      cluster: Number(process.env.CLUSTER_ID ?? 0),
    })

    collectDefaultMetrics({
      register: this.registry,
    })
  }
}
