import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
import random
import asyncio
from typing import Optional, Literal

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snipe_message_author = {}
        self.snipe_message_content = {}
        self.edit_snipe_message_author = {}
        self.edit_snipe_message_content_before = {}
        self.edit_snipe_message_content_after = {}

    async def get_embed(self, ctx, title: str, description: str, color: discord.Color) -> discord.Embed:
        guild_data = self.bot.data.get(str(ctx.guild.id), {})
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        return embed
    
    @app_commands.command(name="userinfo", description="Get information about a user")
    @app_commands.describe(user="The user to get information about (defaults to you)")
    async def userinfo(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Get information about a user"""
        target = user or interaction.user
        guild = interaction.guild
        
        # Get user roles (excluding @everyone)
        roles = [role.mention for role in target.roles if role.name != "@everyone"]
        
        # Get user permissions
        permissions = []
        for perm, value in target.guild_permissions:
            if value and perm not in ['administrator']:  # Skip admin as it's shown separately
                permissions.append(perm.replace('_', ' ').title())
        
        # Get user status
        status = str(target.status).title()
        
        # Get user activity
        activity = None
        if target.activity:
            activity_type = str(target.activity.type).split('.')[-1].title()
            activity = f"{activity_type} {target.activity.name}"
        
        # Get account creation and join dates
        created_at = target.created_at.strftime("%B %d, %Y")
        joined_at = target.joined_at.strftime("%B %d, %Y")
        
        # Calculate account age and server join duration
        account_age = (discord.utils.utcnow() - target.created_at).days
        join_duration = (discord.utils.utcnow() - target.joined_at).days
        
        # Create embed
        embed = await self.get_embed(
            interaction,
            f"User Information: {target}",
            f"**ID:** `{target.id}`\n"
            f"**Bot:** {'✅' if target.bot else '❌'}\n"
            f"**Status:** {status}\n"
            f"**Activity:** {activity or 'None'}\n"
            f"**Account Created:** {created_at} ({account_age} days ago)\n"
            f"**Joined Server:** {joined_at} ({join_duration} days ago)",
            discord.Color.blue()
        )
        
        # Add roles if any
        if roles:
            embed.add_field(
                name=f"Roles ({len(roles)})",
                value=", ".join(roles) if len(", ".join(roles)) < 1024 else f"{len(roles)} roles",
                inline=False
            )
        
        # Add permissions if any
        if permissions:
            if target.guild_permissions.administrator:
                permissions = ["Administrator"]
            
            embed.add_field(
                name="Key Permissions",
                value=", ".join(permissions) if permissions else "No special permissions",
                inline=False
            )
        
        # Add user avatar
        embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="serverinfo", description="Get information about the server")
    async def serverinfo(self, interaction: discord.Interaction):
        """Get information about the server"""
        guild = interaction.guild
        
        # Get server features
        features = [f"`{feature.replace('_', ' ').title()}`" for feature in guild.features]
        
        # Get member status counts
        online = len([m for m in guild.members if m.status == discord.Status.online])
        idle = len([m for m in guild.members if m.status == discord.Status.idle])
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
        offline = len([m for m in guild.members if m.status == discord.Status.offline])
        
        # Get channel counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Get role count (excluding @everyone)
        role_count = len(guild.roles) - 1
        
        # Get server creation date
        created_at = guild.created_at.strftime("%B %d, %Y")
        age_days = (discord.utils.utcnow() - guild.created_at).days
        
        # Create embed
        embed = await self.get_embed(
            interaction,
            f"Server Information: {guild.name}",
            f"**ID:** `{guild.id}`\n"
            f"**Owner:** {guild.owner.mention}\n"
            f"**Created:** {created_at} ({age_days} days ago)\n"
            f"**Members:** {guild.member_count}\n"
            f"**Channels:** {text_channels} text, {voice_channels} voice, {categories} categories\n"
            f"**Roles:** {role_count}\n"
            f"**Boosts:** {guild.premium_subscription_count} (Level {guild.premium_tier})\n"
            f"**Verification Level:** {str(guild.verification_level).title()}\n"
            f"**Features:** {', '.join(features) if features else 'None'}",
            discord.Color.blue()
        )
        
        # Add member status
        embed.add_field(
            name="Member Status",
            value=f"🟢 {online} Online\n"
                 f"🟡 {idle} Idle\n"
                 f"🔴 {dnd} Do Not Disturb\n"
                 f"⚫ {offline} Offline",
            inline=True
        )
        
        # Add server icon if available
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Add banner if available
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="avatar", description="Get a user's avatar")
    @app_commands.describe(user="The user to get the avatar of (defaults to you)")
    async def avatar(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Get a user's avatar"""
        target = user or interaction.user
        
        # Create embed
        embed = await self.get_embed(
            interaction,
            f"{target.name}'s Avatar",
            f"[Download Avatar]({target.avatar.url if target.avatar else target.default_avatar.url})",
            discord.Color.blue()
        )
        
        # Set the image to the user's avatar
        embed.set_image(url=target.avatar.url if target.avatar else target.default_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="snipe", description="Get the last deleted message in this channel")
    async def snipe(self, interaction: discord.Interaction):
        """Get the last deleted message in this channel"""
        channel_id = str(interaction.channel.id)
        
        if channel_id not in self.snipe_message_author:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "No Message Found",
                    "There are no recently deleted messages to snipe in this channel.",
                    discord.Color.orange()
                ),
                ephemeral=True
            )
        
        author = self.snipe_message_author[channel_id]
        content = self.snipe_message_content[channel_id]
        
        # Create embed
        embed = await self.get_embed(
            interaction,
            "Message Sniped",
            f"**Author:** {author.mention}\n**Channel:** {interaction.channel.mention}\n\n{content}",
            discord.Color.blue()
        )
        
        # Add author's avatar
        embed.set_author(name=str(author), icon_url=author.avatar.url if author.avatar else author.default_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="editsnipe", description="Get the last edited message in this channel")
    async def editsnipe(self, interaction: discord.Interaction):
        """Get the last edited message in this channel"""
        channel_id = str(interaction.channel.id)
        
        if channel_id not in self.edit_snipe_message_author:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "No Message Found",
                    "There are no recently edited messages to snipe in this channel.",
                    discord.Color.orange()
                ),
                ephemeral=True
            )
        
        author = self.edit_snipe_message_author[channel_id]
        before = self.edit_snipe_message_content_before[channel_id]
        after = self.edit_snipe_message_content_after[channel_id]
        
        # Create embed
        embed = await self.get_embed(
            interaction,
            "Edit Sniped",
            f"**Author:** {author.mention}\n**Channel:** {interaction.channel.mention}",
            discord.Color.blue()
        )
        
        # Add before and after content
        embed.add_field(name="Before", value=before[:1024] or "*No content*", inline=False)
        embed.add_field(name="After", value=after[:1024] or "*No content*", inline=False)
        
        # Add author's avatar
        embed.set_author(name=str(author), icon_url=author.avatar.url if author.avatar else author.default_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # Ignore DMs and bot messages
        if not message.guild or message.author.bot:
            return
        
        # Store the deleted message
        channel_id = str(message.channel.id)
        self.snipe_message_author[channel_id] = message.author
        self.snipe_message_content[channel_id] = message.content
        
        # Clear the sniped message after 5 minutes
        await asyncio.sleep(300)
        if channel_id in self.snipe_message_author:
            del self.snipe_message_author[channel_id]
            del self.snipe_message_content[channel_id]
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        # Ignore DMs, bot messages, and embeds (to avoid logging embed updates)
        if not before.guild or before.author.bot or before.content == after.content:
            return
        
        # Store the edited message
        channel_id = str(before.channel.id)
        self.edit_snipe_message_author[channel_id] = before.author
        self.edit_snipe_message_content_before[channel_id] = before.content
        self.edit_snipe_message_content_after[channel_id] = after.content
        
        # Clear the sniped message after 5 minutes
        await asyncio.sleep(300)
        if channel_id in self.edit_snipe_message_author:
            del self.edit_snipe_message_author[channel_id]
            del self.edit_snipe_message_content_before[channel_id]
            del self.edit_snipe_message_content_after[channel_id]
    
    @app_commands.command(name="poll", description="Create a simple poll")
    @app_commands.describe(
        question="The question to ask",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)",
        option5="Fifth option (optional)",
        duration="Duration in minutes (default: 5, max: 60)"
    )
    async def poll(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: Optional[str] = None,
        option4: Optional[str] = None,
        option5: Optional[str] = None,
        duration: int = 5
    ):
        """Create a simple poll with up to 5 options"""
        # Validate duration
        duration = max(1, min(duration, 60))  # Clamp between 1 and 60 minutes
        
        # Create options list
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)
        if option5:
            options.append(option5)
        
        # Create poll embed
        embed = await self.get_embed(
            interaction,
            "📊 Poll",
            f"**{question}**\n\n"
            f"React with the corresponding emoji to vote!\n"
            f"Poll ends in {duration} minute{'s' if duration != 1 else ''}.",
            discord.Color.blue()
        )
        
        # Add options
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        options_text = []
        
        for i, option in enumerate(options):
            options_text.append(f"{emojis[i]} {option}")
        
        embed.add_field(name="Options", value="\n".join(options_text), inline=False)
        
        # Set author
        embed.set_author(name=f"Poll by {interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        
        # Send the poll
        message = await interaction.channel.send(embed=embed)
        
        # Add reactions
        for i in range(len(options)):
            await message.add_reaction(emojis[i])
        
        # Send confirmation
        await interaction.response.send_message(
            f"Poll created! [Jump to poll]({message.jump_url})",
            ephemeral=True
        )
        
        # Wait for the poll duration
        await asyncio.sleep(duration * 60)
        
        # Get the updated message with reactions
        try:
            message = await interaction.channel.fetch_message(message.id)
        except:
            return  # Message was deleted
        
        # Count votes
        votes = {}
        total_votes = 0
        
        for i, emoji in enumerate(emojis[:len(options)]):
            for reaction in message.reactions:
                if str(reaction.emoji) == emoji:
                    # Subtract 1 to exclude the bot's reaction
                    vote_count = reaction.count - 1
                    votes[i] = vote_count
                    total_votes += vote_count
                    break
        
        # Create results embed
        results_embed = await self.get_embed(
            interaction,
            "📊 Poll Results",
            f"**{question}**\n\n"
            f"Total votes: {total_votes}",
            discord.Color.green()
        )
        
        # Add results
        results_text = []
        
        for i, option in enumerate(options):
            vote_count = votes.get(i, 0)
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            bar_length = int(percentage / 5)  # 20 segments for 100%
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            results_text.append(
                f"{emojis[i]} **{option}**\n"
                f"{bar} {vote_count} vote{'s' if vote_count != 1 else ''} ({percentage:.1f}%)"
            )
        
        results_embed.add_field(
            name="Results",
            value="\n\n".join(results_text),
            inline=False
        )
        
        # Set author
        results_embed.set_author(name=f"Poll by {interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        
        # Send results
        await message.reply(embed=results_embed)
    
    @app_commands.command(name="remind", description="Set a reminder")
    @app_commands.describe(
        time="Time until reminder (e.g., '10m', '2h', '3d')",
        reminder="What to remind you about"
    )
    async def remind(
        self,
        interaction: discord.Interaction,
        time: str,
        reminder: str
    ):
        """Set a reminder"""
        # Parse time
        try:
            # Get the number and unit
            time_value = int(time[:-1])
            time_unit = time[-1].lower()
            
            # Convert to seconds
            if time_unit == 's':
                seconds = time_value
            elif time_unit == 'm':
                seconds = time_value * 60
            elif time_unit == 'h':
                seconds = time_value * 3600
            elif time_unit == 'd':
                seconds = time_value * 86400
            else:
                raise ValueError("Invalid time unit")
            
            # Validate time (max 30 days)
            if seconds > 30 * 24 * 60 * 60:
                return await interaction.response.send_message(
                    embed=await self.get_embed(
                        interaction,
                        "Error",
                        "Maximum reminder time is 30 days.",
                        discord.Color.red()
                    ),
                    ephemeral=True
                )
            
            # Send confirmation
            time_text = f"{time_value} {self.get_time_unit_name(time_unit, time_value)}"
            
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Reminder Set",
                    f"I'll remind you about this in {time_text}.\n\n"
                    f"**Reminder:** {reminder}",
                    discord.Color.green()
                ),
                ephemeral=True
            )
            
            # Wait for the specified time
            await asyncio.sleep(seconds)
            
            # Send the reminder
            try:
                await interaction.user.send(
                    embed=await self.get_embed(
                        interaction,
                        "⏰ Reminder",
                        f"You asked me to remind you about this {time_text} ago.\n\n"
                        f"**{reminder}**",
                        discord.Color.blue()
                    )
                )
            except:
                # If DM fails, try to send in the channel
                try:
                    await interaction.followup.send(
                        content=f"{interaction.user.mention},",
                        embed=await self.get_embed(
                            interaction,
                            "⏰ Reminder",
                            f"You asked me to remind you about this {time_text} ago.\n\n"
                            f"**{reminder}**",
                            discord.Color.blue()
                        ),
                        ephemeral=True
                    )
                except:
                    pass  # Can't send the reminder
            
        except (ValueError, IndexError):
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Invalid Time Format",
                    "Please use a valid time format. Examples:\n"
                    "`10m` - 10 minutes\n"
                    "`2h` - 2 hours\n"
                    "`1d` - 1 day",
                    discord.Color.red()
                ),
                ephemeral=True
            )
    
    def get_time_unit_name(self, unit: str, value: int) -> str:
        """Get the full name of a time unit"""
        units = {
            's': ('second', 'seconds'),
            'm': ('minute', 'minutes'),
            'h': ('hour', 'hours'),
            'd': ('day', 'days')
        }
        
        if unit not in units:
            return unit
        
        return units[unit][0] if value == 1 else units[unit][1]

    @app_commands.command(name="roleinfo", description="Get information about a role")
    @app_commands.describe(role="The role to get information about")
    async def roleinfo(self, interaction: discord.Interaction, role: discord.Role):
        """Get detailed information about a role"""
        
        # Get role permissions
        perms = [perm.replace('_', ' ').title() for perm, value in role.permissions if value]
        perms_text = ', '.join(perms[:10]) if perms else "No special permissions"
        if len(perms) > 10:
            perms_text += f"... and {len(perms) - 10} more"
        
        embed = await self.get_embed(
            interaction,
            f"Role Info: {role.name}",
            "",
            role.color if role.color != discord.Color.default() else discord.Color.blue()
        )
        
        embed.add_field(name="ID", value=f"`{role.id}`", inline=True)
        embed.add_field(name="Color", value=f"`{str(role.color).upper()}`", inline=True)
        embed.add_field(name="Position", value=f"`{role.position}`", inline=True)
        embed.add_field(name="Members", value=f"`{len(role.members)}`", inline=True)
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(role.created_at, 'R'), inline=False)
        embed.add_field(name="Permissions", value=perms_text, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="emoji", description="Get information about an emoji")
    @app_commands.describe(emoji="The emoji to get information about")
    async def emojiinfo(self, interaction: discord.Interaction, emoji: str):
        """Get information about a server emoji"""
        
        # Try to find the emoji
        found_emoji = None
        for guild_emoji in interaction.guild.emojis:
            if str(guild_emoji) == emoji or guild_emoji.name == emoji:
                found_emoji = guild_emoji
                break
        
        if not found_emoji:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Emoji Not Found",
                    "Could not find that emoji in this server.",
                    discord.Color.red()
                ),
                ephemeral=True
            )
        
        embed = await self.get_embed(
            interaction,
            f"Emoji Info: {found_emoji.name}",
            "",
            discord.Color.blue()
        )
        
        embed.set_thumbnail(url=found_emoji.url)
        embed.add_field(name="Name", value=f"`:{found_emoji.name}:`", inline=True)
        embed.add_field(name="ID", value=f"`{found_emoji.id}`", inline=True)
        embed.add_field(name="Animated", value="Yes" if found_emoji.animated else "No", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(found_emoji.created_at, 'R'), inline=False)
        embed.add_field(name="URL", value=f"[Click Here]({found_emoji.url})", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="invite", description="Get bot invite link")
    async def invite(self, interaction: discord.Interaction):
        """Get the bot's invite link"""
        
        permissions = discord.Permissions(
            administrator=True
        )
        
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=permissions,
            scopes=["bot", "applications.commands"]
        )
        
        embed = await self.get_embed(
            interaction,
            "Invite Synergy Bot",
            f"Click the button below to invite me to your server!",
            discord.Color.blue()
        )
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite Bot", url=invite_url, style=discord.ButtonStyle.link))
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utility(bot))
