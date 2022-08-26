import { Listener } from "@sapphire/framework"
import { GatewayOpcodes, GatewayReceivePayload } from "discord-api-types/v9"

export class RawGatewayPayloadListener extends Listener {
  public constructor(context: Listener.Context, options: Listener.Options) {
    super(context, {
      ...options,
      name: "raw-gateway-payload",
      event: "raw",
    })
  }

  override async run(payload: GatewayReceivePayload, shard: number) {
    if (payload.op !== GatewayOpcodes.Dispatch) return

    this.container.metrics.gatewayDispatchEvents.inc({
      event: payload.t,
      shard,
    })
  }
}
