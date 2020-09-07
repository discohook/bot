def wrap_in_code(value: str):
    value = value.replace("`", "\u200b`\u200b")
    value = value.replace("\u200b\u200b", "\u200b")
    value = "``" + value + "``"
    return value
