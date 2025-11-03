import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

class ReactionRoleEmbedModal(discord.ui.Modal, title="Reaction Role Embed Builder"):
    """Modal for creating reaction role embed"""
    title_input = discord.ui.TextInput(
        label="Embed Title",
        placeholder="Select Your Roles",
        required=True,
        max_length=256
    )
    description = discord.ui.TextInput(
        label="Description",
        placeholder="React below to get roles!",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=4000
    )
    color = discord.ui.TextInput(
        label="Color (hex code)",
        placeholder="#5865F2",
        required=False,
        max_length=7
    )
    footer = discord.ui.TextInput(
        label="Footer Text",
        placeholder="Click reactions to get roles",
        required=False,
        max_length=2048
    )
    
    def __init__(self, bot, message_id: str):
        super().__init__()
        self.bot = bot
        self.message_id = message_id
    
    async def on_submit(self, interaction: discord.Interaction):
        # Get color
        color_hex = self.color.value or "#5865F2"
        try:
            color = discord.Color(int(color_hex.replace('#', ''), 16))
        except:
            color = discord.Color.blue()
        
        # Create embed
        embed = discord.Embed(
            title=self.title_input.value,
            description=self.description.value or None,
            color=color
        )
        
        # Set footer
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        footer_text = self.footer.value or guild_data.get('footer_text', 'Synergy Bot')
        footer_icon = guild_data.get('footer_icon', '')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send message and store ID
        message = await interaction.channel.send(embed=embed)
        
        # Store reaction role panel
        if 'reaction_roles' not in guild_data:
            guild_data['reaction_roles'] = {}
        
        guild_data['reaction_roles'][str(message.id)] = {
            'roles': {},
            'channel_id': interaction.channel.id
        }
        
        self.bot.data[str(interaction.guild.id)] = guild_data
        self.bot.save_data()
        
        await interaction.response.send_message(
            f"✅ Reaction role panel created!\n"
            f"**Message ID:** `{message.id}`\n\n"
            f"Use `/reactionrole add message_id:{message.id} emoji:😀 role:@Role` to add roles!",
            ephemeral=True
        )

class ReactionRoles(commands.Cog):
    """Reaction role system for self-assignable roles"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def get_reaction_role_data(self, guild_id: int) -> dict:
        """Get all reaction role panels for a guild"""
        guild_data = self.bot.data.get(str(guild_id), {})
        return guild_data.get('reaction_roles', {})
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle reaction add"""
        if payload.user_id == self.bot.user.id or not payload.guild_id:
            return
        
        guild_data = self.bot.data.get(str(payload.guild_id), {})
        reaction_roles = guild_data.get('reaction_roles', {})
        
        message_data = reaction_roles.get(str(payload.message_id))
        if not message_data:
            return
        
        # Get emoji string
        if payload.emoji.id:
            emoji_str = f"<:{payload.emoji.name}:{payload.emoji.id}>"
        else:
            emoji_str = payload.emoji.name
        
        # Check if this emoji has a role
        role_id = message_data['roles'].get(emoji_str)
        if not role_id:
            return
        
        # Add role to user
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        role = guild.get_role(role_id)
        
        if member and role:
            try:
                await member.add_roles(role, reason="Reaction role")
            except:
                pass
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Handle reaction remove"""
        if payload.user_id == self.bot.user.id or not payload.guild_id:
            return
        
        guild_data = self.bot.data.get(str(payload.guild_id), {})
        reaction_roles = guild_data.get('reaction_roles', {})
        
        message_data = reaction_roles.get(str(payload.message_id))
        if not message_data:
            return
        
        # Get emoji string
        if payload.emoji.id:
            emoji_str = f"<:{payload.emoji.name}:{payload.emoji.id}>"
        else:
            emoji_str = payload.emoji.name
        
        # Check if this emoji has a role
        role_id = message_data['roles'].get(emoji_str)
        if not role_id:
            return
        
        # Remove role from user
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        role = guild.get_role(role_id)
        
        if member and role:
            try:
                await member.remove_roles(role, reason="Reaction role removed")
            except:
                pass
    
    @app_commands.command(name="reactionrolepanel", description="Create a reaction role panel")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def create_panel(self, interaction: discord.Interaction):
        """Create a new reaction role panel"""
        modal = ReactionRoleEmbedModal(self.bot, "new")
        await interaction.response.send_modal(modal)
    
    @app_commands.command(name="reactionrole", description="Add or remove reaction role")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(
        action="Add or remove a reaction role (add/remove)",
        message_id="ID of the reaction role message",
        emoji="Emoji to react with",
        role="Role to assign (required for add action)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Add", value="add"),
        app_commands.Choice(name="Remove", value="remove")
    ])
    async def reaction_role(
        self,
        interaction: discord.Interaction,
        action: str,
        message_id: str,
        emoji: str,
        role: Optional[discord.Role] = None
    ):
        """Add or remove reaction roles"""
        if action not in ["add", "remove"]:
            await interaction.response.send_message("Invalid action. Please use 'add' or 'remove'.", ephemeral=True)
            return
            
        if action == "add" and role is None:
            await interaction.response.send_message("Role is required when adding a reaction role.", ephemeral=True)
            return
            
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        
        if 'reaction_roles' not in guild_data:
            guild_data['reaction_roles'] = {}
        
        reaction_roles = guild_data['reaction_roles']
        
        if str(message_id) not in reaction_roles:
            return await interaction.response.send_message("Message ID not found! Create a panel first.", ephemeral=True)
        
        message_data = reaction_roles[str(message_id)]
        
        if action == 'add':
            if not role:
                return await interaction.response.send_message("Please provide a role!", ephemeral=True)
            
            # Add role mapping
            message_data['roles'][emoji] = role.id
            
            # Add reaction to message
            channel = interaction.guild.get_channel(message_data['channel_id'])
            if channel:
                try:
                    message = await channel.fetch_message(int(message_id))
                    await message.add_reaction(emoji)
                except:
                    pass
            
            self.bot.data[str(interaction.guild.id)] = guild_data
            self.bot.save_data()
            
            await interaction.response.send_message(
                f"✅ Added reaction role: {emoji} → {role.mention}",
                ephemeral=True
            )
        
        elif action == 'remove':
            if emoji in message_data['roles']:
                del message_data['roles'][emoji]
                
                self.bot.data[str(interaction.guild.id)] = guild_data
                self.bot.save_data()
                
                await interaction.response.send_message(f"✅ Removed reaction role for {emoji}", ephemeral=True)
            else:
                await interaction.response.send_message(f"No reaction role found for {emoji}", ephemeral=True)
    
    @app_commands.command(name="reactionrolelist", description="List all reaction role panels")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def list_panels(self, interaction: discord.Interaction):
        """List all reaction role panels"""
        reaction_roles = self.get_reaction_role_data(interaction.guild.id)
        
        if not reaction_roles:
            return await interaction.response.send_message("No reaction role panels configured!", ephemeral=True)
        
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        
        embed = discord.Embed(
            title="📋 Reaction Role Panels",
            color=discord.Color.blue()
        )
        
        for message_id, data in reaction_roles.items():
            channel = interaction.guild.get_channel(data['channel_id'])
            roles_info = []
            
            for emoji, role_id in data['roles'].items():
                role = interaction.guild.get_role(role_id)
                if role:
                    roles_info.append(f"{emoji} → {role.mention}")
            
            field_value = "\n".join(roles_info) if roles_info else "No roles configured"
            embed.add_field(
                name=f"Message ID: {message_id}",
                value=f"**Channel:** {channel.mention if channel else 'Unknown'}\n{field_value}",
                inline=False
            )
        
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
