import discord
from discord.ui import Button, View, Select

class LFGView(View):
    """The interactive buttons for signing up."""
    def __init__(self, creator: discord.Member, dungeon: str, level: int, initial_role: str, looking_for: list):
        super().__init__(timeout=3600)
        self.creator = creator
        self.dungeon = dungeon
        self.level = level
        self.looking_for = looking_for
        self.slots = {"Tank": None, "Healer": None, "DPS": []}

        if initial_role == "Tank":
            self.slots["Tank"] = creator
        elif initial_role == "Healer":
            self.slots["Healer"] = creator
        elif initial_role == "DPS":
            self.slots["DPS"].append(creator)

        self._update_button_states()

    def _update_button_states(self):
        """Dynamically updates buttons if a role is full or wasn't requested."""
        self.tank_button.disabled = ("Tank" not in self.looking_for) or (self.slots["Tank"] is not None)
        self.healer_button.disabled = ("Healer" not in self.looking_for) or (self.slots["Healer"] is not None)
        
        dps_requested = sum(1 for role in self.looking_for if role.startswith("DPS"))
        is_host_dps = 1 if self.creator in self.slots["DPS"] else 0
        target_dps_count = min(3, is_host_dps + dps_requested)
        
        self.dps_button.disabled = (dps_requested == 0) or (len(self.slots["DPS"]) >= target_dps_count)

    def is_user_in_group(self, user: discord.Member) -> bool:
        """Helper to check if a user is already in any slot"""
        if user == self.slots["Tank"]: return True
        if user == self.slots["Healer"]: return True
        if user in self.slots["DPS"]: return True
        return False

    def create_embed(self):
        embed = discord.Embed(
            title=f"{self.dungeon} +{self.level}",
            description=f"Host: {self.creator.mention}\nClick a button below to join!",
            color=discord.Color.red()
        )

        # --- Tank ---
        if self.slots["Tank"]:
            tank_val = self.slots["Tank"].mention
        elif "Tank" not in self.looking_for:
            tank_val = "*Filled*"
        else:
            tank_val = "Empty"

        # --- Healer ---
        if self.slots["Healer"]:
            heal_val = self.slots["Healer"].mention
        elif "Healer" not in self.looking_for:
            heal_val = "*Filled*"
        else:
            heal_val = "Empty"

        # --- DPS ---
        dps_list = [m.mention for m in self.slots["DPS"]]

        dps_requested = sum(1 for role in self.looking_for if role.startswith("DPS"))
        is_host_dps = 1 if self.creator in self.slots["DPS"] else 0
        target_dps_count = min(3, is_host_dps + dps_requested)

        while len(dps_list) < target_dps_count:
            dps_list.append("Empty")

        while len(dps_list) < 3:
            dps_list.append("*Filled*")

        # Add embeds 
        embed.add_field(name="Tank", value=tank_val, inline=True)
        embed.add_field(name="Healer", value=heal_val, inline=True)
        embed.add_field(name="DPS", value="\n".join(dps_list), inline=True)

        return embed
    
    async def on_timeout(self):
        """Called automatically when the timeout expires."""
        for child in self.children:
            child.disabled = True
        
        if self.message:
            embed = self.create_embed()
            embed.color = discord.Color.dark_gray()
            embed.set_footer(text="This group has timed out.")
            try:
                await self.message.edit(embed=embed, view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Tank", style=discord.ButtonStyle.blurple)
    async def tank_button(self, interaction: discord.Interaction, button: Button):
        if self.is_user_in_group(interaction.user):
            return await interaction.response.send_message("You are already in this group!", ephemeral=True)
        self.slots["Tank"] = interaction.user
        self._update_button_states()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Healer", style=discord.ButtonStyle.green)
    async def healer_button(self, interaction: discord.Interaction, button: Button):
        if self.is_user_in_group(interaction.user):
            return await interaction.response.send_message("You are already in this group!", ephemeral=True)
        self.slots["Healer"] = interaction.user
        self._update_button_states()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="DPS", style=discord.ButtonStyle.red)
    async def dps_button(self, interaction: discord.Interaction, button: Button):
        if self.is_user_in_group(interaction.user):
            return await interaction.response.send_message("You are already in this group!", ephemeral=True)        
        self.slots["DPS"].append(interaction.user)
        self._update_button_states()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Allows the host to delete the group posting."""
        if interaction.user != self.creator:
            return await interaction.response.send_message("Only the group host can cancel this run!", ephemeral=True)
        await interaction.message.delete()
        self.stop()



class LFGSetupView(View):
    """The ephemeral setup menu presented to the user after typing /lfg"""
    def __init__(self, dungeon: str, level: int):
        super().__init__(timeout=300)
        self.dungeon = dungeon
        self.level = level
        self.my_role = None
        self.looking_for = []

    @discord.ui.select(placeholder="Select your role", row=0, options=[
        discord.SelectOption(label="Tank"),
        discord.SelectOption(label="Healer"),
        discord.SelectOption(label="DPS")
    ])
    async def select_my_role(self, interaction: discord.Interaction, select: Select):
        self.my_role = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(placeholder="What roles are you looking for?", row=1, min_values=1, max_values=5, options=[
        discord.SelectOption(label="Tank"),
        discord.SelectOption(label="Healer"),
        discord.SelectOption(label="DPS", value="DPS 1"),
        discord.SelectOption(label="DPS", value="DPS 2"),
        discord.SelectOption(label="DPS", value="DPS 3")
    ])
    async def select_looking_for(self, interaction: discord.Interaction, select: Select):
        self.looking_for = select.values
        await interaction.response.defer()
    
    @discord.ui.button(label="Create Group", style=discord.ButtonStyle.green, row=2)
    async def btn_create(self, interaction: discord.Interaction, button: Button):
        if not self.my_role or not self.looking_for:
            return await interaction.response.send_message("Please select an option from all dropdown menus before creating the group.", ephemeral=True)
        public_view = LFGView(
            creator=interaction.user,
            dungeon=self.dungeon,
            level=self.level,
            initial_role=self.my_role,
            looking_for=self.looking_for
        )
        msg = await interaction.channel.send(
            content=f"{interaction.user.mention} is looking for more!",
            embed=public_view.create_embed(),
            view=public_view
        )
        public_view.message = msg
        await interaction.response.edit_message(content="Group created successfully!", view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, row=2)
    async def btn_cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(content="Group creation cancelled.", view=None)
