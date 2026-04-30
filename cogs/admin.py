import discord
from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync(self, ctx):
        """Syncs slash commands to the current server instantly"""
        print("Syncing commands...")
        self.bot.tree.copy_global_to(guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"DungeonSlave has synced commands to **{ctx.guild.name}**")

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Safely shuts down the bot."""
        await ctx.send("DungeonSlave going offline.")
        await self.bot.close()
    
    @commands.Cog.listener()
    async def on_command_error(ctx, error):
        """Prevents the terminal from flooding with errors if non-admin uses ! commands."""
        if isinstance(error, commands.NotOwner):
            await ctx.send("You do not have permission to use admin commands.", delete_after=5)
        else:
            raise error
    
async def setup(bot):
    await bot.add_cog(Admin(bot))