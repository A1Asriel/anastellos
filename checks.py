from discord import HTTPException
from nextcord.ext import commands


async def soft_reply(self, content=None, **kwargs):
    try:
        return await self.message.reply(content, **kwargs)
    except HTTPException:
        return await self.channel.send(content, **kwargs)


async def reply_or_send(ctx: commands.Context):
    if not ctx.channel.permissions_for(ctx.me).read_message_history:
        ctx.reply = ctx.send
    else:
        ctx.reply = soft_reply.__get__(ctx, commands.Context)


async def is_eula_accepted(ctx: commands.Context):
    if not ctx.bot.config.demand_agreement:
        value = True
    else:
        guild_cfg = ctx.bot.guild_config.get_guild_cfg(ctx.guild.id)
        if guild_cfg is None:
            value = False
        else:
            value: bool = guild_cfg.is_eula_accepted
    if not value:
        await ctx.bot.get_command("privacy").__call__(ctx)
    return value


def is_cog_enabled(ctx: commands.Context):
    guild_cfg = ctx.bot.guild_config.get_guild_cfg(ctx.guild.id)
    if guild_cfg is None:
        return True
    return ctx.cog.qualified_name not in guild_cfg.disabled_cogs
