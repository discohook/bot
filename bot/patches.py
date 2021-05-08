import discord


def patch_fail_if_not_exists(cls):
    orig = cls.to_message_reference_dict

    cls.to_message_reference_dict = lambda self: {
        **orig(self),
        "fail_if_not_exists": False,
    }


for cls in (discord.Message, discord.MessageReference):
    patch_fail_if_not_exists(cls)
