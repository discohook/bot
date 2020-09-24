from typing import Optional, Union


def wrap_in_code(value: str, *, block: Optional[Union[bool, str]] = None):
    value = value.replace("`", "\u200b`\u200b")
    value = value.replace("\u200b\u200b", "\u200b")

    if block is None:
        return "``" + value + "``"

    lang = "" if block is True else block

    return f"```{block}\n" + value + "\n```"
