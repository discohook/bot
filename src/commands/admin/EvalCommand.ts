import { Args, Command, PieceContext } from "@sapphire/framework"
import { Message, PermissionFlagsBits } from "discord.js"
import { createRequire } from "node:module"
import { resolve } from "node:path"
import { inspect } from "node:util"
import { runInNewContext } from "node:vm"

export class EvalCommand extends Command {
  constructor(context: PieceContext) {
    super(context, {
      name: "eval",
      quotes: [],
      preconditions: ["owner-only"],
      requiredClientPermissions: [PermissionFlagsBits.AttachFiles],
      detailedDescription: {},
    })
  }

  async #sendFile(message: Message, value: unknown, fileName: string) {
    return message.reply({
      files: [
        {
          attachment: Buffer.from(
            inspect(value, { depth: Infinity, colors: true }).replace(
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
    code = "(async function* () {\n" + match[3] + "\n})()"

    try {
      const generator = runInNewContext(code, {
        ...this.container,
        message,
        author: message.author,
        member: message.member,
        channel: message.channel,
        guild: message.guild,
        require: createRequire(resolve(__dirname, "..", "..", "eval.js")),
      }) as AsyncGenerator<unknown, unknown, unknown>

      let result: IteratorResult<unknown, unknown>
      while ((result = await generator.next())) {
        await this.#sendFile(message, result.value, "result.ansi")
        if (result.done) break
      }
    } catch (error) {
      await this.#sendFile(message, error, "error.ansi")
    }
  }
}
