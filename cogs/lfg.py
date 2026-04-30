import discord
from discord import app_commands
from discord.ext import commands

from config import DUNGEON_CHOICES
from views.lfg_views import LFGSetupView

class LFG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lfg", description="Create a dungeon group")
    @app_commands.describe(
        dungeon="Select the dungeon",
        level="Select the key level"
    )
    @app_commands.choices(dungeon=DUNGEON_CHOICES)
    async def lfg(self, interaction: discord.Interaction, dungeon: app_commands.Choice[str], level: app_commands.Range[int, 2, 25]):
        setup_view = LFGSetupView(dungeon=dungeon.value, level=level)
        await interaction.response.send_message(
            content=f"Setting up group for **{dungeon.value} +{level}**:",
            view=setup_view,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(LFG(bot))