import discord
import os
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View


# Load secret token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# --- DATA & Utilities --- 

DUNGEON_ALIASES = {
    "aa": "Algeth'ar Academy",
    "mc": "Maisara Caverns",
    "mt": "Magisters' Terrace",
    "pos": "Pit of Saron",
    "ws": "Windrunner Spire",
    "seat": "Seat of the Triumvirate",
    "npx": "Nexus-Point Xenas",
    "sr": "Skyreach"
}

def resolve_dungeon(name: str) -> str:
    name_lower = name.lower().strip()
    return DUNGEON_ALIASES.get(name_lower, name.title())


# --- UI Elements ---

class LFGView(View):
    """The interactive buttons for signing up."""
    def __init__(self, creator: discord.Member, dungeon: str, level: int):
        super().__init__(timeout=None)
        self.creator = creator
        self.dungeon = dungeon
        self.level = level
        self.slots = {"Tank": None, "Healer": None, "DPS": []}

    def create_embed(self):
        embed = discord.Embed(
            title=f"New Mythic+ Run: {self.dungeon} + {self.level}",
            description=f"Host: {self.creator.mention}\nClick a button below to join!",
            color=discord.Color.blue()
        )

        tank_val = self.slots["Tank"].mention if self.slots["Tank"] else "Empty"
        heal_val = self.slots["Healer"].mention if self.slots["Healer"] else "Empty"
        dps_list = [m.mention for m in self.slots["DPS"]]
        while len(dps_list) < 3:
            dps_list.append("Empty")

        embed.add_field(name="Tank", value=tank_val, inline=True)
        embed.add_field(name="Healer", value=heal_val, inline=True)
        embed.add_field(name="DPS", value="\n".join(dps_list), inline=True)

        return embed
    
    @discord.ui.button(label="Tank", style=discord.ButtonStyle.green)
    async def tank_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.slots["Tank"]:
            return await interaction.response.send_message("Tank slot is full!", ephemeral=True)
        self.slots["Tank"] = interaction.user
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Healer", style=discord.ButtonStyle.green)
    async def healer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.slots["Healer"]:
            return await interaction.response.send_message("Healer slot is full!", ephemeral=True)
        self.slots["Healer"] = interaction.user
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="DPS", style=discord.ButtonStyle.green)
    async def dps_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.slots["DPS"]) >= 3:
            return await interaction.response.send_message("DPS slots are full!", ephemeral=True)
        if interaction.user in self.slots["DPS"]:
            return await interaction.response.send_message("You are already signed up!", ephemeral=True)
        
        self.slots["DPS"].append(interaction.user)
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
    

# --- DungeonSlave Class ---

class DungeonSlave(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("--- DungeonSlave Admin Mode ---")
        print("Bot initialised. Use !sync to update slash commands.")
        bot.tree.copy_global_to(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)

    async def on_ready(self):
        print(f"Loggin in as: {self.user.name}")
        print(f"ID: {self.user.id}")
        print("-----------------------")

bot = DungeonSlave()


# --- Admin only commands, ! prefix ---

@bot.command(name="sync")
@commands.is_owner()
async def sync(ctx):
    """Syncs slash commands to the current server instantly"""
    print("Syncing commands...")
    bot.tree.copy_global_to(guild=ctx.guild)
    await bot.tree.sync(guild=ctx.guild)
    await ctx.send(f"DungeonSlave has synced commands to **{ctx.guild.name}**")

@bot.command(name="shutdown")
@commands.is_owner()
async def shutdown(ctx):
    """Safly shuts down the bot."""
    await ctx.send("DungeonSlave going offline.")
    await bot.close()


# --- Public commands, slash commands ---

@bot.tree.command(name="lfg", description="Create a dungeon group")
@app_commands.describe(
    dungeon="Name or alias (e.g., AA)",
    level="Key level",
    my_role="Your role"
)
@app_commands.choices(my_role=[
    app_commands.Choice(name="Tank", value="Tank"),
    app_commands.Choice(name="Healer", value="Healer"),
    app_commands.Choice(name="DPS", value="DPS")
])
async def lfg(interaction: discord.Interaction, dungeon: str, level: int, my_role: app_commands.Choice[str]):
    real_dungeon = resolve_dungeon(dungeon)

    view = LFGView(interaction.user, real_dungeon, level)

    if my_role.value == "Tank":
        view.slots["Tank"] = interaction.user
    elif my_role.value == "Healer":
        view.slots["Healer"] = interaction.user
    else:
        view.slots["DPS"].append(interaction.user)

    await interaction.response.send_message(
        content=f"{interaction.user.display_name} is looking for more!",
        embed=view.create_embed(),
        view=view
    )




# --- Error Handling ---

@bot.event
async def on_command_error(ctx, error):
    """Prevents the terminal from flooding with errors if non-admin uses ! commands."""
    if isinstance(error, commands.NotOwner):
        await ctx.send("You do not have permission to use admin commands.", delete_after=5)
    else:
        raise error




# Launch 

if __name__ == "__main__":
    bot.run(TOKEN)