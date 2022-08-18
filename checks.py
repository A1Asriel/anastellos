from nextcord.ext import commands

async def reply_or_send(ctx: commands.Context):
    if not ctx.channel.permissions_for(ctx.me).read_message_history:
        ctx.reply = ctx.send