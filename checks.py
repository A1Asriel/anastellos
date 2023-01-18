from nextcord.ext import commands


async def reply_or_send(ctx: commands.Context):
    if not ctx.channel.permissions_for(ctx.me).read_message_history:
        ctx.reply = ctx.send


def is_eula_accepted(ctx: commands.Context):
    if not ctx.bot.config.demand_agreement:
        return True
    guild_cfg = ctx.bot.guild_config.get_guild_cfg(ctx.guild.id)
    if guild_cfg is None:
        return False
    return guild_cfg.is_eula_accepted

def is_cog_enabled(ctx: commands.Context):
    guild_cfg = ctx.bot.guild_config.get_guild_cfg(ctx.guild.id)
    if guild_cfg is None:
        return True
    return ctx.cog.qualified_name not in guild_cfg.disabled_cogs
