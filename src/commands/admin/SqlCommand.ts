import { Args, Command, PieceContext } from "@sapphire/framework"
import { Message, PermissionFlagsBits } from "discord.js"
import { inspect } from "node:util"

export class SqlCommand extends Command {
  constructor(context: PieceContext) {
    super(context, {
      name: "sql",
      quotes: [],
      preconditions: ["owner-only"],
      requiredClientPermissions: [PermissionFlagsBits.AttachFiles],
      detailedDescription: {},
    })
  }

  async #sendFile(message: Message, object: unknown, fileName: string) {
    return message.reply({
      files: [
        {
          attachment: Buffer.from(
            inspect(object, { depth: Infinity, colors: true }).replace(
              /\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])/g,
              (match) =>
                /\x1B\[(?:\d+(?:[:;]\d+)*)m/.test(match)
                  ? "\x1B[0m" + match
                  : match === "\x1B[m"
                  ? "\x1B[0m"
                  : "",
            ),
            "utf-8",
          ),
          name: fileName,
        },
      ],
    })
  }

  override async messageRun(message: Message, args: Args) {
    let code = await args.rest("string")
    const match = /^(?:(`{1,3})([\w-]*\n)?)?(.*)\1$/su.exec(code)
    if (!match) return
    code = match[3]

    try {
      const result = await this.container.database.raw(code)
      await this.#sendFile(message, result.rows, "result.ansi")
    } catch (error) {
      await this.#sendFile(message, error, "error.ansi")
    }
  }
}
