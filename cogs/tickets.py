import discord
from discord import app_commands, ui
from discord.ext import commands, tasks
import asyncio
import random
import string
import json
import datetime
import os
from typing import Optional, List, Dict, Union, Literal, Any
from dataclasses import dataclass, field
from enum import Enum

# Enums for ticket status and priority
class TicketStatus(Enum):
    OPEN = "open"
    PENDING = "pending"
    CLOSED = "closed"
    LOCKED = "locked"
    SOLVED = "solved"

class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# Data class for ticket configuration
@dataclass
class TicketConfig:
    guild_id: int
    category_id: int
    support_roles: List[int] = field(default_factory=list)
    ping_roles: List[int] = field(default_factory=list)
    ticket_message: str = "Thank you for creating a ticket! A staff member will be with you shortly."
    ticket_title: str = "New Ticket"
    button_emoji: Optional[str] = None
    button_color: str = "blurple"
    require_topic: bool = False
    custom_id: str = field(default_factory=lambda: str(random.randint(1000, 9999)))
    max_tickets: int = 3
    allow_user_close: bool = True
    send_transcript: bool = True
    archive_category: Optional[int] = None
    auto_close: bool = False
    auto_close_hours: int = 48

class CategorySelectView(ui.View):
    """View with dropdown for selecting ticket category"""
    def __init__(self, bot, categories: List[Dict]):
        super().__init__(timeout=None)
        self.bot = bot
        self.categories = categories
        
        # Create select menu with categories
        options = []
        for cat in categories[:25]:  # Discord limit
            emoji = cat.get('emoji', '🎫')
            options.append(
                discord.SelectOption(
                    label=cat['name'],
                    description=cat.get('description', 'Select this category')[:100],
                    emoji=emoji,
                    value=cat['id']
                )
            )
        
        select = ui.Select(
            placeholder="🎫 Select a ticket category...",
            options=options,
            custom_id="ticket_category_select"
        )
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        category_id = interaction.data['values'][0]
        category = next((c for c in self.categories if c['id'] == category_id), None)
        
        if not category:
            return await interaction.response.send_message("Category not found.", ephemeral=True)
        
        # Check if user already has open tickets
        cog = self.bot.get_cog('EnhancedTickets')
        existing = [t for t in cog.tickets.values() 
                   if t.get('creator_id') == interaction.user.id and t.get('status') == 'open']
        
        if len(existing) >= 3:
            return await interaction.response.send_message(
                "❌ You already have 3 open tickets. Please close one before creating another.",
                ephemeral=True
            )
        
        # Check blacklist
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        blacklist = guild_data.get('ticket_blacklist', [])
        if interaction.user.id in blacklist:
            return await interaction.response.send_message(
                "❌ You are blacklisted from creating tickets.",
                ephemeral=True
            )
        
        # Show modal or create ticket directly
        if category.get('custom_questions'):
            modal = CategoryTicketModal(self.bot, category)
            await interaction.response.send_modal(modal)
        else:
            # Create ticket directly without modal
            await interaction.response.defer(ephemeral=True)
            await cog.create_ticket_channel(interaction, category, "No topic provided", "No description provided")

class CategoryTicketModal(ui.Modal):
    """Modal with custom questions for ticket category"""
    def __init__(self, bot, category: Dict):
        super().__init__(title=f"Create {category['name']} Ticket")
        self.bot = bot
        self.category = category
        
        # Add custom questions
        questions = category.get('custom_questions', [])
        
        if questions:
            for i, question in enumerate(questions[:5]):  # Max 5 inputs
                style = discord.TextStyle.paragraph if question.get('long_answer') else discord.TextStyle.short
                text_input = ui.TextInput(
                    label=question['question'][:45],
                    placeholder=question.get('placeholder', '')[:100],
                    style=style,
                    required=question.get('required', True),
                    max_length=1000 if question.get('long_answer') else 100
                )
                self.add_item(text_input)
        else:
            # Default questions
            self.add_item(ui.TextInput(
                label="Topic",
                placeholder="Brief description...",
                style=discord.TextStyle.short,
                required=True,
                max_length=100
            ))
            self.add_item(ui.TextInput(
                label="Details",
                placeholder="Provide more information...",
                style=discord.TextStyle.paragraph,
                required=False,
                max_length=1000
            ))
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Collect answers
        answers = []
        for item in self.children:
            if isinstance(item, ui.TextInput):
                answers.append(f"**{item.label}:** {item.value}")
        
        topic = self.children[0].value if self.children else "New Ticket"
        description = "\n".join(answers)
        
        # Create ticket
        cog = self.bot.get_cog('EnhancedTickets')
        if cog:
            await cog.create_ticket_channel(interaction, self.category, topic, description)

class CloseReasonModal(ui.Modal, title="Close Ticket"):
    """Modal to get close reason"""
    reason = ui.TextInput(
        label="Reason for closing",
        placeholder="Why are you closing this ticket?",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500
    )
    
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        cog = self.bot.get_cog('EnhancedTickets')
        if cog:
            await cog.close_ticket_helper(interaction, self.reason.value or "No reason provided")

class RatingView(ui.View):
    """View for ticket rating"""
    def __init__(self, bot, ticket_data: dict):
        super().__init__(timeout=300)  # 5 minute timeout
        self.bot = bot
        self.ticket_data = ticket_data
    
    @ui.button(label="⭐", style=discord.ButtonStyle.gray, custom_id="rate_1")
    async def rate_1(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_rating(interaction, 1)
    
    @ui.button(label="⭐⭐", style=discord.ButtonStyle.gray, custom_id="rate_2")
    async def rate_2(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_rating(interaction, 2)
    
    @ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.gray, custom_id="rate_3")
    async def rate_3(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_rating(interaction, 3)
    
    @ui.button(label="⭐⭐⭐⭐", style=discord.ButtonStyle.gray, custom_id="rate_4")
    async def rate_4(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_rating(interaction, 4)
    
    @ui.button(label="⭐⭐⭐⭐⭐", style=discord.ButtonStyle.green, custom_id="rate_5")
    async def rate_5(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_rating(interaction, 5)
    
    async def handle_rating(self, interaction: discord.Interaction, rating: int):
        """Handle rating submission"""
        await interaction.response.send_message(
            f"✅ Thank you for rating this ticket {rating}/5 stars!",
            ephemeral=True
        )
        
        # Log rating
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if log_channel_id:
            log_channel = interaction.guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="⭐ Ticket Rated",
                    description=f"**User:** {interaction.user.mention}\n"
                               f"**Ticket:** {self.ticket_data.get('topic', 'Unknown')}\n"
                               f"**Rating:** {rating}/5 stars",
                    color=discord.Color.gold()
                )
                await log_channel.send(embed=embed)
        
        self.stop()

class TicketControlView(ui.View):
    """Persistent view for ticket control buttons"""
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @ui.button(label="Close", style=discord.ButtonStyle.red, emoji="🔒", custom_id="ticket_close_btn")
    async def close_button(self, interaction: discord.Interaction, button: ui.Button):
        """Close the ticket"""
        # Show close reason modal
        modal = CloseReasonModal(self.bot)
        await interaction.response.send_modal(modal)
    
    @ui.button(label="Claim", style=discord.ButtonStyle.green, emoji="✋", custom_id="ticket_claim_btn")
    async def claim_button(self, interaction: discord.Interaction, button: ui.Button):
        """Claim the ticket"""
        ticket = self.bot.get_cog('EnhancedTickets').tickets.get(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message("This is not a ticket channel.", ephemeral=True)
        
        if ticket.get('claimed_by'):
            claimer = interaction.guild.get_member(ticket['claimed_by'])
            return await interaction.response.send_message(
                f"This ticket is already claimed by {claimer.mention if claimer else 'someone'}.",
                ephemeral=True
            )
        
        ticket['claimed_by'] = interaction.user.id
        self.bot.get_cog('EnhancedTickets').save_data()
        
        await interaction.response.send_message(f"✅ {interaction.user.mention} has claimed this ticket!")
    
    @ui.button(label="Transcript", style=discord.ButtonStyle.gray, emoji="📄", custom_id="ticket_transcript_btn")
    async def transcript_button(self, interaction: discord.Interaction, button: ui.Button):
        """Generate transcript"""
        cog = self.bot.get_cog('EnhancedTickets')
        if cog:
            await cog.generate_transcript_helper(interaction)

class TicketCreationModal(ui.Modal, title="Create a Ticket"):
    """Modal for ticket creation with custom fields"""
    def __init__(self, bot, panel_name: str = "default"):
        super().__init__()
        self.bot = bot
        self.panel_name = panel_name
    
    topic = ui.TextInput(
        label="What do you need help with?",
        placeholder="Briefly describe your issue...",
        style=discord.TextStyle.short,
        required=True,
        max_length=100
    )
    description = ui.TextInput(
        label="Detailed Description",
        placeholder="Provide more details about your issue...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Get ticket cog
        cog = self.bot.get_cog('EnhancedTickets')
        if not cog:
            return await interaction.followup.send("Ticket system not loaded.", ephemeral=True)
        
        # Get or create category
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        category_id = guild_data.get('ticket_category')
        
        if category_id:
            category = interaction.guild.get_channel(category_id)
        else:
            category = discord.utils.get(interaction.guild.categories, name="Tickets")
            if not category:
                category = await interaction.guild.create_category("Tickets")
                guild_data['ticket_category'] = category.id
                self.bot.save_data()
        
        # Create ticket channel
        ticket_channel = await category.create_text_channel(
            f"ticket-{interaction.user.name}",
            topic=self.topic.value,
            reason=f"Ticket created by {interaction.user}"
        )
        
        # Set permissions
        await ticket_channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await ticket_channel.set_permissions(interaction.user, view_channel=True, send_messages=True)
        
        # Add support roles
        support_roles = guild_data.get('ticket_support_roles', [])
        for role_id in support_roles:
            role = interaction.guild.get_role(role_id)
            if role:
                await ticket_channel.set_permissions(role, view_channel=True, send_messages=True)
        
        # Save ticket data
        ticket_data = {
            'guild_id': interaction.guild.id,
            'creator_id': interaction.user.id,
            'created_at': datetime.datetime.utcnow().isoformat(),
            'status': 'open',
            'topic': self.topic.value,
            'description': self.description.value or "No description provided",
            'panel': self.panel_name,
            'participants': [interaction.user.id]
        }
        
        cog.tickets[ticket_channel.id] = ticket_data
        cog.save_data()
        
        # Send welcome message
        embed = discord.Embed(
            title=f"🎫 Ticket: {self.topic.value}",
            description=f"**Created by:** {interaction.user.mention}\n"
                       f"**Topic:** {self.topic.value}\n"
                       f"**Description:** {self.description.value or 'No description provided'}\n\n"
                       f"A staff member will be with you shortly.",
            color=discord.Color.green()
        )
        
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        view = TicketControlView(self.bot)
        await ticket_channel.send(f"{interaction.user.mention}", embed=embed, view=view)
        
        await interaction.followup.send(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)

class EnhancedTickets(commands.Cog):
    """Advanced ticket system with support for multiple ticket types, transcripts, and more."""
    
    def __init__(self, bot):
        self.bot = bot
        self.ticket_cooldown = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.user)
        self.active_views = set()
        self.ticket_configs: Dict[int, Dict[str, TicketConfig]] = {}
        self.tickets: Dict[int, dict] = {}
        self.ticket_counter: Dict[int, int] = {}  # Guild ID -> counter
        self.load_data()
        self.cleanup_task = self.cleanup_old_tickets.start()
        
        # Register persistent views
        self.bot.add_view(TicketControlView(bot))
    
    def cog_unload(self):
        self.cleanup_task.cancel()
    
    def load_data(self):
        """Load ticket data from the database."""
        if os.path.exists('tickets.json'):
            with open('tickets.json', 'r') as f:
                data = json.load(f)
                self.tickets = {int(k): v for k, v in data.get('tickets', {}).items()}
    
    def save_data(self):
        """Save ticket data to the database."""
        with open('tickets.json', 'w') as f:
            json.dump({'tickets': self.tickets}, f, indent=2)
    
    @tasks.loop(hours=1)
    async def cleanup_old_tickets(self):
        """Clean up old closed tickets."""
        now = datetime.datetime.utcnow()
        to_remove = []
        
        for channel_id, ticket in self.tickets.items():
            if ticket.get('status') == 'closed':
                closed_at = datetime.datetime.fromisoformat(ticket.get('closed_at'))
                if (now - closed_at).days > 7:  # Keep closed tickets for 7 days
                    to_remove.append(channel_id)
        
        for channel_id in to_remove:
            del self.tickets[channel_id]
        
        if to_remove:
            self.save_data()
    
    async def create_ticket_channel(self, interaction: discord.Interaction, category: dict, topic: str, description: str):
        """Create a ticket channel"""
        # Get guild data
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        
        # Get or create ticket category
        category_id = category.get('category_id') or guild_data.get('ticket_category')
        if category_id:
            ticket_category = interaction.guild.get_channel(category_id)
        else:
            ticket_category = discord.utils.get(interaction.guild.categories, name="Tickets")
            if not ticket_category:
                ticket_category = await interaction.guild.create_category("Tickets")
                guild_data['ticket_category'] = ticket_category.id
                self.bot.save_data()
        
        # Get ticket counter
        guild_id = interaction.guild.id
        if guild_id not in self.ticket_counter:
            self.ticket_counter[guild_id] = 0
        self.ticket_counter[guild_id] += 1
        ticket_num = self.ticket_counter[guild_id]
        
        # Create channel with category-number naming
        channel_name = f"{category.get('name', 'ticket').lower().replace(' ', '-')}-{ticket_num:04d}"
        
        ticket_channel = await ticket_category.create_text_channel(
            channel_name,
            topic=topic,
            reason=f"Ticket created by {interaction.user}"
        )
        
        # Set permissions
        await ticket_channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await ticket_channel.set_permissions(interaction.user, view_channel=True, send_messages=True)
        
        # Add support roles and ping roles
        support_roles = category.get('support_roles', []) or guild_data.get('ticket_support_roles', [])
        ping_roles = category.get('ping_roles', [])
        
        pings = []
        for role_id in support_roles:
            role = interaction.guild.get_role(role_id)
            if role:
                await ticket_channel.set_permissions(role, view_channel=True, send_messages=True)
        
        for role_id in ping_roles:
            role = interaction.guild.get_role(role_id)
            if role:
                pings.append(role.mention)
        
        # Save ticket data
        ticket_data = {
            'guild_id': interaction.guild.id,
            'creator_id': interaction.user.id,
            'created_at': datetime.datetime.utcnow().isoformat(),
            'status': 'open',
            'category': category['id'],
            'category_name': category['name'],
            'topic': topic,
            'description': description,
            'ticket_number': ticket_num,
            'participants': [interaction.user.id]
        }
        
        self.tickets[ticket_channel.id] = ticket_data
        self.save_data()
        
        # Send welcome message
        welcome_msg = category.get('welcome_message', 
            f"Thank you for contacting support, {interaction.user.mention}!\n\n"
            f"**Topic:** {topic}\n\n"
            f"Please describe your issue and a staff member will be with you shortly.")
        
        embed = discord.Embed(
            title=f"🎫 {category['name']} Ticket #{ticket_num:04d}",
            description=description,
            color=discord.Color.from_str(category.get('color', '#5865F2'))
        )
        embed.add_field(name="Created by", value=interaction.user.mention, inline=True)
        embed.add_field(name="Status", value="🟢 Open", inline=True)
        
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        ping_text = " ".join(pings) if pings else ""
        view = TicketControlView(self.bot)
        await ticket_channel.send(content=f"{interaction.user.mention} {ping_text}".strip(), embed=embed, view=view)
        
        # Notify user
        try:
            await interaction.followup.send(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)
        except:
            pass
    
    @app_commands.command(name="ticketpanel", description="Create an advanced ticket panel with categories")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        title="Title of the ticket panel",
        description="Description shown in the panel",
        channel="Channel to send the panel to"
    )
    async def ticket_panel(
        self, 
        interaction: discord.Interaction, 
        title: str = "🎫 Support Tickets",
        description: str = "Select a category below to create a ticket",
        channel: Optional[discord.TextChannel] = None
    ):
        """Create a ticket panel with category dropdown"""
        channel = channel or interaction.channel
        
        # Get categories from guild data
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        categories = guild_data.get('ticket_categories', [])
        
        if not categories:
            # Create default categories
            categories = [
                {
                    'id': 'general',
                    'name': 'General Support',
                    'description': 'Get help with general inquiries',
                    'emoji': '💬',
                    'color': '#5865F2'
                },
                {
                    'id': 'bugs',
                    'name': 'Bug Report',
                    'description': 'Report a bug or issue',
                    'emoji': '🐛',
                    'color': '#ED4245'
                },
                {
                    'id': 'other',
                    'name': 'Other',
                    'description': 'Something else',
                    'emoji': '📝',
                    'color': '#FEE75C'
                }
            ]
            guild_data['ticket_categories'] = categories
            self.bot.save_data()
        
        # Create embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )
        
        # Add category info to embed
        category_info = []
        for cat in categories:
            emoji = cat.get('emoji', '🎫')
            category_info.append(f"{emoji} **{cat['name']}** - {cat.get('description', 'No description')}")
        
        embed.add_field(name="Available Categories", value="\n".join(category_info), inline=False)
        
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Create view with dropdown
        view = CategorySelectView(self.bot, categories)
        
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"✅ Ticket panel with {len(categories)} categories created in {channel.mention}!",
            ephemeral=True
        )
    
    @app_commands.command(name="adduser", description="Add a user to the ticket")
    @app_commands.describe(user="The user to add to the ticket")
    async def add_user(self, interaction: discord.Interaction, user: discord.Member):
        """Add a user to the current ticket."""
        ticket = self.tickets.get(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message("This is not a ticket channel.", ephemeral=True)
        
        if user.id in ticket['participants']:
            return await interaction.response.send_message("User is already in this ticket.", ephemeral=True)
        
        # Add user to ticket
        await interaction.channel.set_permissions(user, read_messages=True, send_messages=True)
        ticket['participants'].append(user.id)
        self.save_data()
        
        await interaction.response.send_message(f"Added {user.mention} to the ticket.")
    
    async def close_ticket_helper(self, interaction: discord.Interaction, close_reason: str = "No reason provided"):
        """Helper method for closing tickets (used by button and command)"""
        ticket = self.tickets.get(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message("This is not a ticket channel.", ephemeral=True)
        
        # Generate transcript before closing
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if log_channel_id:
            log_channel = interaction.guild.get_channel(log_channel_id)
            if log_channel:
                # Create transcript
                messages = []
                async for message in interaction.channel.history(limit=1000, oldest_first=True):
                    timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    messages.append(f"[{timestamp}] {message.author}: {message.content}")
                
                transcript = "\n".join(messages)
                
                # Save to file temporarily
                filename = f"transcript-{interaction.channel.id}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Ticket Transcript - {interaction.channel.name}\n")
                    f.write(f"Closed by: {interaction.user}\n")
                    f.write(f"Closed at: {datetime.datetime.utcnow()}\n")
                    f.write("="*50 + "\n\n")
                    f.write(transcript)
                
                # Send to log channel
                try:
                    with open(filename, 'rb') as f:
                        file = discord.File(f, filename)
                        embed = discord.Embed(
                            title="🎫 Ticket Closed",
                            description=f"**Ticket:** {interaction.channel.name}\n**Closed by:** {interaction.user.mention}",
                            color=discord.Color.red()
                        )
                        await log_channel.send(embed=embed, file=file)
                finally:
                    # Clean up file
                    try:
                        await asyncio.sleep(0.5)  # Small delay to ensure file handle is closed
                        os.remove(filename)
                    except:
                        pass
        
        # Update ticket status
        ticket['status'] = 'closed'
        ticket['closed_by'] = interaction.user.id
        ticket['closed_at'] = datetime.datetime.utcnow().isoformat()
        self.save_data()
        
        # Update close reason
        ticket['close_reason'] = close_reason
        
        # Send rating request to ticket creator
        creator = interaction.guild.get_member(ticket['creator_id'])
        if creator and creator != interaction.user:
            try:
                rating_view = RatingView(self.bot, ticket)
                await creator.send(
                    f"Your ticket **{ticket.get('topic', 'Ticket')}** has been closed.\n"
                    f"**Reason:** {close_reason}\n\n"
                    f"Please rate your experience:",
                    view=rating_view
                )
            except:
                pass
        
        # Notify and delete channel
        await interaction.followup.send(f"✅ This ticket has been closed.\n**Reason:** {close_reason}\n\nChannel will be deleted in 5 seconds...")
        await asyncio.sleep(5)
        
        # Remove from tickets dict
        del self.tickets[interaction.channel.id]
        self.save_data()
        
        # Delete the channel
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        except:
            pass
    
    @app_commands.command(name="close", description="Close the current ticket")
    @app_commands.describe(reason="Reason for closing the ticket")
    async def close_ticket(self, interaction: discord.Interaction, reason: Optional[str] = None):
        """Close the current ticket."""
        if reason:
            await self.close_ticket_helper(interaction, reason)
        else:
            # Show modal for reason
            modal = CloseReasonModal(self.bot)
            await interaction.response.send_modal(modal)
    
    @app_commands.command(name="ticketblacklist", description="Blacklist a user from creating tickets")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(user="The user to blacklist", remove="Set to True to remove from blacklist")
    async def ticket_blacklist(self, interaction: discord.Interaction, user: discord.Member, remove: bool = False):
        """Blacklist or unblacklist a user from creating tickets"""
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        
        if 'ticket_blacklist' not in guild_data:
            guild_data['ticket_blacklist'] = []
        
        blacklist = guild_data['ticket_blacklist']
        
        if remove:
            if user.id in blacklist:
                blacklist.remove(user.id)
                self.bot.save_data()
                await interaction.response.send_message(f"✅ {user.mention} has been removed from the ticket blacklist.", ephemeral=True)
            else:
                await interaction.response.send_message(f"{user.mention} is not blacklisted.", ephemeral=True)
        else:
            if user.id not in blacklist:
                blacklist.append(user.id)
                self.bot.save_data()
                await interaction.response.send_message(f"✅ {user.mention} has been blacklisted from creating tickets.", ephemeral=True)
            else:
                await interaction.response.send_message(f"{user.mention} is already blacklisted.", ephemeral=True)
    
    @app_commands.command(name="ticketstats", description="View ticket statistics")
    async def ticket_stats(self, interaction: discord.Interaction):
        """View server ticket statistics"""
        guild_tickets = [t for t in self.tickets.values() if t.get('guild_id') == interaction.guild.id]
        
        open_tickets = len([t for t in guild_tickets if t.get('status') == 'open'])
        total_tickets = self.ticket_counter.get(interaction.guild.id, 0)
        
        # Count by category
        category_counts = {}
        for ticket in guild_tickets:
            cat = ticket.get('category_name', 'Unknown')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        embed = discord.Embed(
            title="📊 Ticket Statistics",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Open Tickets", value=f"```{open_tickets}```", inline=True)
        embed.add_field(name="Total Created", value=f"```{total_tickets}```", inline=True)
        embed.add_field(name="Closed", value=f"```{total_tickets - open_tickets}```", inline=True)
        
        if category_counts:
            cat_text = "\n".join([f"**{cat}:** {count}" for cat, count in category_counts.items()])
            embed.add_field(name="By Category", value=cat_text, inline=False)
        
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        await interaction.response.send_message(embed=embed)
    
    async def generate_transcript_helper(self, interaction: discord.Interaction):
        """Helper method for generating transcripts (used by button and command)"""
        ticket = self.tickets.get(interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message("This is not a ticket channel.", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        
        # Get log channel
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return await interaction.followup.send("No log channel configured. Use `/setup` to set one.", ephemeral=True)
        
        log_channel = interaction.guild.get_channel(log_channel_id)
        if not log_channel:
            return await interaction.followup.send("Log channel not found.", ephemeral=True)
        
        # Create a detailed transcript
        messages = []
        async for message in interaction.channel.history(limit=1000, oldest_first=True):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            messages.append(f"[{timestamp}] {message.author}: {message.content}")
        
        transcript = "\n".join(messages)
        
        # Save to file
        filename = f"transcript-{interaction.channel.id}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Ticket Transcript - {interaction.channel.name}\n")
            f.write(f"Generated by: {interaction.user}\n")
            f.write(f"Generated at: {datetime.datetime.utcnow()}\n")
            f.write("="*50 + "\n\n")
            f.write(transcript)
        
        # Send to log channel
        try:
            with open(filename, 'rb') as f:
                file = discord.File(f, filename)
                embed = discord.Embed(
                    title="📄 Ticket Transcript",
                    description=f"**Ticket:** {interaction.channel.name}\n**Generated by:** {interaction.user.mention}",
                    color=discord.Color.blue()
                )
                await log_channel.send(embed=embed, file=file)
            
            await interaction.followup.send(f"✅ Transcript sent to {log_channel.mention}", ephemeral=True)
        finally:
            # Clean up file with proper delay
            try:
                await asyncio.sleep(0.5)  # Small delay to ensure file handle is closed
                os.remove(filename)
            except Exception as e:
                # If deletion fails, just log it and continue
                pass

    @app_commands.command(name="transcript", description="Generate a transcript of the ticket")
    async def generate_transcript(self, interaction: discord.Interaction):
        """Generate a transcript of the current ticket."""
        await self.generate_transcript_helper(interaction)

async def setup(bot):
    await bot.add_cog(EnhancedTickets(bot))
