from nextcord.ext import commands

from ..classes import AEEmbed, AnastellosInternalCog
from ..utils import *


class Info(AnastellosInternalCog):
    @commands.command(aliases=['info'])
    @commands.guild_only()
    async def about(self, ctx: commands.Context):
        l10n = localization(self.bot, guild_id=ctx.guild.id)[
            'anastellos']['info']['about']
        title = f'{self.bot.config.name} {self.bot.config.full_version}'
        desc = l10n['desc'].format(prefix=ctx.clean_prefix)
        if self.bot.config.mode == 2:
            desc += l10n['indev']
        creator = await self.bot.fetch_user(self.bot.owner_id)
        footer_title = l10n['creator'].format(creator=creator)
        footer_icon = creator.display_avatar.url
        thumbnail = self.bot.config.self_avatar_url
        author_name = l10n['anastellos']
        author_icon = 'https://cdn.discordapp.com/attachments/713481949896900622/992450921852313640/anastellos_engine_logo.png'
        author_url = 'https://github.com/A1Asriel/anastellos/'
        await ctx.send(embed=AEEmbed(self.bot,
                                     title=title,
                                     desc=desc,
                                     footer_title=footer_title,
                                     footer_icon=footer_icon,
                                     thumbnail_url=thumbnail,
                                     author_name=author_name,
                                     author_icon=author_icon,
                                     author_url=author_url)
                       )


def setup(bot):
    bot.add_cog(Info(bot))
