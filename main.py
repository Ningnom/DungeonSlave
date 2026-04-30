import discord
import os 
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

class DungeonSlave(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("--- DungeonSlave Admin Mode ---")
        
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.lfg")

        print("Bot initialised. Use !sync to update slash commands.")

    async def on_ready(self):
        print(f"Logging in as: {self.user.name}")
        print(f"ID: {self.user.id}")
        print("------------------------")

if __name__ == "__main__":
    bot = DungeonSlave()
    bot.run(TOKEN)