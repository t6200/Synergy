import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from typing import Optional

class WelcomeEmbedModal(discord.ui.Modal, title="Welcome Embed Builder"):
    """Modal for building welcome embed"""
    title_input = discord.ui.TextInput(
        label="Embed Title",
        placeholder="Welcome to {server}!",
        required=False,
        max_length=256
    )
    description = discord.ui.TextInput(
        label="Description",
        placeholder="Welcome {user}! You are member #{member_count}",
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
        placeholder="Enjoy your stay!",
        required=False,
        max_length=2048
    )
    image_url = discord.ui.TextInput(
        label="Image URL (optional)",
        placeholder="https://i.imgur.com/example.png",
        required=False
    )
    
    def __init__(self, bot, embed_type: str):
        super().__init__()
        self.bot = bot
        self.embed_type = embed_type  # 'welcome' or 'goodbye'
    
    async def on_submit(self, interaction: discord.Interaction):
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        
        if self.embed_type not in guild_data:
            guild_data[self.embed_type] = {}
        
        guild_data[self.embed_type]['title'] = self.title_input.value or None
        guild_data[self.embed_type]['description'] = self.description.value or None
        guild_data[self.embed_type]['color'] = self.color.value or "#5865F2"
        guild_data[self.embed_type]['footer'] = self.footer.value or None
        guild_data[self.embed_type]['image_url'] = self.image_url.value or None
        
        self.bot.data[str(interaction.guild.id)] = guild_data
        self.bot.save_data()
        
        await interaction.response.send_message(
            f"✅ {self.embed_type.title()} embed configured!\n\n"
            f"**Variables you can use:**\n"
            f"`{{user}}` - User mention\n"
            f"`{{username}}` - Username\n"
            f"`{{server}}` - Server name\n"
            f"`{{member_count}}` - Member count\n"
            f"`{{user_id}}` - User ID",
            ephemeral=True
        )

class WelcomeGoodbye(commands.Cog):
    """Welcome and goodbye message system with customizable embeds"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def format_message(self, text: str, member: discord.Member) -> str:
        """Format message with variables"""
        return text.replace('{user}', member.mention) \
                   .replace('{username}', str(member)) \
                   .replace('{server}', member.guild.name) \
                   .replace('{member_count}', str(member.guild.member_count)) \
                   .replace('{user_id}', str(member.id))
    
    def create_embed(self, config: dict, member: discord.Member, guild_data: dict) -> discord.Embed:
        """Create embed from configuration"""
        # Get color
        color_hex = config.get('color', '#5865F2')
        try:
            color = discord.Color(int(color_hex.replace('#', ''), 16))
        except:
            color = discord.Color.blue()
        
        # Create embed
        embed = discord.Embed(color=color, timestamp=datetime.utcnow())
        
        # Set title
        if config.get('title'):
            embed.title = self.format_message(config['title'], member)
        
        # Set description
        if config.get('description'):
            embed.description = self.format_message(config['description'], member)
        
        # Set footer
        footer_text = config.get('footer')
        if footer_text:
            footer_text = self.format_message(footer_text, member)
        else:
            footer_text = guild_data.get('footer_text', 'Synergy Bot')
        
        footer_icon = guild_data.get('footer_icon', '')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Set thumbnail to user avatar
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Set image if provided
        if config.get('image_url'):
            embed.set_image(url=config['image_url'])
        
        return embed
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Send welcome message when member joins"""
        guild_data = self.bot.data.get(str(member.guild.id), {})
        welcome_config = guild_data.get('welcome', {})
        
        if not welcome_config.get('enabled', False):
            return
        
        channel_id = welcome_config.get('channel')
        if not channel_id:
            return
        
        channel = member.guild.get_channel(channel_id)
        if not channel:
            return
        
        try:
            # Create and send embed
            embed = self.create_embed(welcome_config, member, guild_data)
            
            # Get custom message if any
            message_content = welcome_config.get('message')
            if message_content:
                message_content = self.format_message(message_content, member)
            
            await channel.send(content=message_content, embed=embed)
            
            # Auto-role if configured
            autorole_id = welcome_config.get('autorole')
            if autorole_id:
                role = member.guild.get_role(autorole_id)
                if role:
                    try:
                        await member.add_roles(role, reason="Auto-role on join")
                    except:
                        pass
        
        except Exception as e:
            pass
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Send goodbye message when member leaves"""
        guild_data = self.bot.data.get(str(member.guild.id), {})
        goodbye_config = guild_data.get('goodbye', {})
        
        if not goodbye_config.get('enabled', False):
            return
        
        channel_id = goodbye_config.get('channel')
        if not channel_id:
            return
        
        channel = member.guild.get_channel(channel_id)
        if not channel:
            return
        
        try:
            # Create and send embed
            embed = self.create_embed(goodbye_config, member, guild_data)
            
            # Get custom message if any
            message_content = goodbye_config.get('message')
            if message_content:
                message_content = self.format_message(message_content, member)
            
            await channel.send(content=message_content, embed=embed)
        
        except Exception as e:
            pass
    
    @app_commands.command(name="welcomesetup", description="Setup welcome messages")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        enabled="Enable or disable welcome messages",
        channel="Channel to send welcome messages",
        autorole="Role to give new members automatically"
    )
    async def welcome_setup(
        self,
        interaction: discord.Interaction,
        enabled: Optional[bool] = None,
        channel: Optional[discord.TextChannel] = None,
        autorole: Optional[discord.Role] = None
    ):
        """Configure welcome message settings"""
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        
        if 'welcome' not in guild_data:
            guild_data['welcome'] = {}
        
        if enabled is not None:
            guild_data['welcome']['enabled'] = enabled
        
        if channel:
            guild_data['welcome']['channel'] = channel.id
        
        if autorole:
            guild_data['welcome']['autorole'] = autorole.id
        
        self.bot.data[str(interaction.guild.id)] = guild_data
        self.bot.save_data()
        
        # Show current configuration
        welcome_config = guild_data['welcome']
        
        embed = discord.Embed(
            title="👋 Welcome Message Configuration",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Status",
            value="✅ Enabled" if welcome_config.get('enabled') else "❌ Disabled",
            inline=True
        )
        
        if welcome_config.get('channel'):
            ch = interaction.guild.get_channel(welcome_config['channel'])
            embed.add_field(name="Channel", value=ch.mention if ch else "Not set", inline=True)
        
        if welcome_config.get('autorole'):
            role = interaction.guild.get_role(welcome_config['autorole'])
            embed.add_field(name="Auto-Role", value=role.mention if role else "Not set", inline=True)
        
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="welcomeembed", description="Customize welcome embed")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_embed(self, interaction: discord.Interaction):
        """Open embed builder for welcome message"""
        modal = WelcomeEmbedModal(self.bot, 'welcome')
        await interaction.response.send_modal(modal)
    
    @app_commands.command(name="goodbyesetup", description="Setup goodbye messages")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        enabled="Enable or disable goodbye messages",
        channel="Channel to send goodbye messages"
    )
    async def goodbye_setup(
        self,
        interaction: discord.Interaction,
        enabled: Optional[bool] = None,
        channel: Optional[discord.TextChannel] = None
    ):
        """Configure goodbye message settings"""
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        
        if 'goodbye' not in guild_data:
            guild_data['goodbye'] = {}
        
        if enabled is not None:
            guild_data['goodbye']['enabled'] = enabled
        
        if channel:
            guild_data['goodbye']['channel'] = channel.id
        
        self.bot.data[str(interaction.guild.id)] = guild_data
        self.bot.save_data()
        
        # Show current configuration
        goodbye_config = guild_data['goodbye']
        
        embed = discord.Embed(
            title="👋 Goodbye Message Configuration",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="Status",
            value="✅ Enabled" if goodbye_config.get('enabled') else "❌ Disabled",
            inline=True
        )
        
        if goodbye_config.get('channel'):
            ch = interaction.guild.get_channel(goodbye_config['channel'])
            embed.add_field(name="Channel", value=ch.mention if ch else "Not set", inline=True)
        
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="goodbyeembed", description="Customize goodbye embed")
    @app_commands.checks.has_permissions(administrator=True)
    async def goodbye_embed(self, interaction: discord.Interaction):
        """Open embed builder for goodbye message"""
        modal = WelcomeEmbedModal(self.bot, 'goodbye')
        await interaction.response.send_modal(modal)
    
    @app_commands.command(name="testwelcome", description="Test welcome message")
    @app_commands.checks.has_permissions(administrator=True)
    async def test_welcome(self, interaction: discord.Interaction):
        """Test the welcome message with your user"""
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        welcome_config = guild_data.get('welcome', {})
        
        if not welcome_config:
            return await interaction.response.send_message("Welcome messages not configured!", ephemeral=True)
        
        try:
            embed = self.create_embed(welcome_config, interaction.user, guild_data)
            
            message_content = welcome_config.get('message')
            if message_content:
                message_content = self.format_message(message_content, interaction.user)
            
            await interaction.response.send_message(content=message_content, embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error creating embed: {e}", ephemeral=True)
    
    @app_commands.command(name="testgoodbye", description="Test goodbye message")
    @app_commands.checks.has_permissions(administrator=True)
    async def test_goodbye(self, interaction: discord.Interaction):
        """Test the goodbye message with your user"""
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        goodbye_config = guild_data.get('goodbye', {})
        
        if not goodbye_config:
            return await interaction.response.send_message("Goodbye messages not configured!", ephemeral=True)
        
        try:
            embed = self.create_embed(goodbye_config, interaction.user, guild_data)
            
            message_content = goodbye_config.get('message')
            if message_content:
                message_content = self.format_message(message_content, interaction.user)
            
            await interaction.response.send_message(content=message_content, embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error creating embed: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WelcomeGoodbye(bot))
