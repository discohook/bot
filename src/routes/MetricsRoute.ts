import { ApiRequest, ApiResponse, methods, Route } from "@sapphire/plugin-api"

export class MetricsRoute extends Route {
  public constructor(context: Route.Context, options: Route.Options) {
    super(context, {
      ...options,
      name: "metrics",
      route: "metrics",
    })
  }

  public async [methods.GET](_request: ApiRequest, response: ApiResponse) {
    response.setHeader(
      "Content-Type",
      this.container.metrics.registry.contentType,
    )
    response.text(await this.container.metrics.registry.metrics())
  }
}
