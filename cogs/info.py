import nextcord
from nextcord.ext import commands
from ..classes import AnastellosCog, AEEmbed
from ..utils import *


class Info(AnastellosCog):
    @commands.command(aliases = ['info'])
    @commands.guild_only()
    async def about(self, ctx: commands.Context):
        l10n = localization(guild_id=ctx.guild.id)['anastellos']['info']['about']
        title = f'{self.bot.config.name} {self.bot.config.full_version}'
        desc = l10n['desc'].format(prefix=get_prefix(self.bot, ctx.message))
        if self.bot.config.mode == 'indev':
            desc += l10n['indev']
        creator = await self.bot.fetch_user(296735247213789215)
        footer_title = l10n['creator'].format(creator=creator)
        footer_icon = creator.display_avatar.url
        thumbnail = self.bot.config.self_avatar_url
        author_name = l10n['anastellos']
        author_icon = self.bot.config.anastellos_logo
        await ctx.send(embed=AEEmbed(self.bot,
                                     title=title,
                                     desc=desc,
                                     footer_title=footer_title,
                                     footer_icon=footer_icon,
                                     thumbnail_url=thumbnail,
                                     author_name=author_name,
                                     author_icon=author_icon)
                       )

    @commands.command()
    async def changelog(self, ctx: commands.Context, *, filter='normal'):
        class ChangelogUI(nextcord.ui.View):
            def __init__(self, ctx: commands.Context, patches, lang, page=1):
                super().__init__(timeout=180)
                self.ctx = ctx
                self.patches = patches
                self.lang = lang
                if len(patches) > 25:
                    self.page = page
                    self.max_page = len(patches) // 25 + 1
                    self.add_item(SelectPatch(patches[25*(self.page - 1) : 25*self.page]))
                    self.add_item(PageControls('◀️', self))
                    self.add_item(PageControls('▶️', self))
                else:
                    self.add_item(SelectPatch(patches))

            async def update(self):
                self.clear_items()
                self.add_item(SelectPatch(self.patches[25*(self.page - 1) : 25*self.page]))
                self.add_item(PageControls('◀️', self))
                self.add_item(PageControls('▶️', self))
                
                l10n = localization(lang=self.lang)['anastellos']['info']['changelog']
                fields = []
                for ver in self.patches[25*(self.page - 1) : 25*self.page]:
                    fields.append((ver['fullname'], ver.get(self.lang, ver['en'])['desc']))
                embed = AEEmbed(ctx.bot, title=l10n['title'], fields=fields)
                await self.message.edit(view=self, embed=embed)
                return

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                try:
                    await self.message.edit(view=self, embed=self.message.embeds[0])
                except nextcord.NotFound:
                    pass
                return None

            async def interaction_check(self, interaction: nextcord.Interaction):
                if self.ctx.author == interaction.user:
                    return True
                else:
                    return False


        class SelectPatch(nextcord.ui.Select):
            def __init__(self, patches) -> None:
                self.patches = patches
                super().__init__()
                for i, patch in enumerate(self.patches):
                    self.add_option(label=patch['fullname'], value=i)

            async def callback(self, interaction: nextcord.Interaction):
                patch = self.patches[int(self.values[0])]
                desc = patch.get(self.view.lang, patch['en'])['desc']
                changes = '\n'.join(patch.get(self.view.lang, patch['en'])['changes'])
                desc = f'{desc}\n\n{changes}'
                embed = AEEmbed(interaction.client, title=patch['fullname'], desc=desc)
                await self.view.message.edit(embed=embed, view=None)
                self.view.stop()
                return


        class PageControls(nextcord.ui.Button):
            def __init__(self, emoji, view):
                super().__init__(emoji=emoji, style=nextcord.ButtonStyle.primary)
                self._view = view
                if emoji == '▶️' and self.view.page == self.view.max_page:
                    self.disabled = True
                elif emoji == '◀️' and self.view.page == 1:
                    self.disabled = True

            async def callback(self, interaction: nextcord.Interaction):
                if self.emoji.name=='▶️':
                    self.view.page += 1
                elif self.emoji.name=='◀️':
                    self.view.page -= 1
                await self.view.update()
                return


        filter = filter.lower().split(' ')
        l10n = localization(guild_id=ctx.guild.id)['anastellos']['info']['changelog']
        lang = fetch_json('server_cfg')[str(ctx.guild.id)]['lang']
        try:
            chglog = fetch_json('jsons/changelog')
        except:
            raise commands.CommandInvokeError

        filtered = {}
        keys = ('type', 'stage', 'version', 'build')

        for ver in chglog:
            for key in keys:
                if 'all' in filter or chglog[ver][key] in filter:
                    filtered[ver] = chglog[ver]
                    break
        filtered = list(filtered.values())
        if not filtered:
            embed = AEEmbed(self.bot, title=l10n['title'], desc=l10n['no_patches'])
            return await ctx.reply(embed=embed)
        fields = []
        for ver in filtered[:25]:
            fields.append((ver['fullname'], ver.get(lang, ver['en'])['desc']))
        embed = AEEmbed(self.bot, title=l10n['title'], fields=fields)
        _ChangelogUI = ChangelogUI(ctx, filtered, lang)
        msg = await ctx.reply(embed=embed, view=_ChangelogUI)
        _ChangelogUI.message = msg

def setup(bot):
    bot.add_cog(Info(bot))