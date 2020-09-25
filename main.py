import os

import bot

os.environ.setdefault("JISHAKU_HIDE", "true")
os.environ.setdefault("JISHAKU_NO_UNDERSCORE", "true")


def main():
    app = bot.Bot()
    app.run(os.environ.get("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
