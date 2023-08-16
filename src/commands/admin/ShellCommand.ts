import { Args, Command, type PieceContext } from "@sapphire/framework"
import { Message, PermissionFlagsBits } from "discord.js"
import { spawn } from "node:child_process"

export class ShellCommand extends Command {
  constructor(context: PieceContext) {
    super(context, {
      name: "shell",
      quotes: [],
      preconditions: ["owner-only"],
      requiredClientPermissions: [PermissionFlagsBits.AttachFiles],
      detailedDescription: {},
    })
  }

  override async messageRun(message: Message, args: Args) {
    let code = await args.rest("string")
    const match = /^(?:(`{1,3})([\w-]*\n)?)?(.*)\1$/su.exec(code)
    if (!match) return
    code = match[3]

    const child = spawn("sh", ["-c", code], {
      stdio: ["ignore", "pipe", "pipe"],
    })

    let output = ""
    for (const stream of [child.stdout, child.stderr]) {
      stream.on("data", (chunk) => (output += chunk))
    }

    const status = await new Promise<number | NodeJS.Signals>((resolve) => {
      child.on("close", (code, signal) => resolve(code ?? signal!))
    })

    output = output.replace(
      /\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])/g,
      (match) =>
        /\x1B\[(?:\d+(?:[:;]\d+)*)m/.test(match)
          ? "\x1B[0m" + match
          : match === "\x1B[m"
          ? "\x1B[0m"
          : "",
    )

    await message.reply({
      files: [
        {
          attachment: Buffer.from(`Status: ${status}\n\n` + output, "utf-8"),
          name: "result.ansi",
        },
      ],
    })
  }
}
