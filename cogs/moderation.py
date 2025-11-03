import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import asyncio
from typing import Optional

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mute_tasks = {}

    def cog_unload(self):
        for task in self.mute_tasks.values():
            task.cancel()

    async def get_mod_embed(self, ctx, title: str, description: str, color: discord.Color) -> discord.Embed:
        guild_data = self.bot.data.get(str(ctx.guild.id), {})
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        return embed

    @app_commands.command(name="tempban", description="Temporarily ban a user from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(
        user="The user to ban",
        duration="Duration (e.g., 1d, 12h, 30m)",
        reason="The reason for the ban"
    )
    async def tempban(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str = "No reason provided"):
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    "You cannot ban someone with an equal or higher role.",
                    discord.Color.red()
                )
            )

        try:
            await user.ban(reason=f"{interaction.user} (ID: {interaction.user.id}): {reason}")
            
            # Log the ban
            await self.log_action(
                interaction.guild,
                "Member Temporarily Banned",
                f"**User:** {user.mention} (ID: {user.id})\n**Moderator:** {interaction.user.mention}\n**Duration:** {duration}\n**Reason:** {reason}",
                discord.Color.red()
            )
            
            # Schedule unban
            await self.schedule_unban(interaction.guild, user, duration)
            
            await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Member Temporarily Banned",
                    f"{user.mention} has been banned for {duration}.\n**Reason:** {reason}",
                    discord.Color.green()
                )
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    f"Failed to ban user: {str(e)}",
                    discord.Color.red()
                )
            )

    async def schedule_unban(self, guild, user, duration: str):
        """Schedule an unban after the specified duration"""
        # Parse duration
        try:
            if duration.endswith('d'):
                seconds = int(duration[:-1]) * 86400
            elif duration.endswith('h'):
                seconds = int(duration[:-1]) * 3600
            elif duration.endswith('m'):
                seconds = int(duration[:-1]) * 60
            else:
                return
            
            await asyncio.sleep(seconds)
            
            try:
                await guild.unban(user, reason="Temporary ban expired")
                await self.log_action(
                    guild,
                    "Member Unbanned",
                    f"**User:** {user.mention} (ID: {user.id})\n**Reason:** Temporary ban expired",
                    discord.Color.green()
                )
            except:
                pass
        except:
            pass

    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(
        user="The user to ban",
        reason="The reason for the ban"
    )
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    "You cannot ban someone with an equal or higher role.",
                    discord.Color.red()
                )
            )

        try:
            await user.ban(reason=f"{interaction.user} (ID: {interaction.user.id}): {reason}")
            
            # Log the ban
            await self.log_action(
                interaction.guild,
                "Member Banned",
                f"**User:** {user.mention} (ID: {user.id})\n**Moderator:** {interaction.user.mention}\n**Reason:** {reason}",
                discord.Color.red()
            )
            
            await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Member Banned",
                    f"{user.mention} has been banned.\n**Reason:** {reason}",
                    discord.Color.green()
                )
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    f"Failed to ban user: {str(e)}",
                    discord.Color.red()
                )
            )

    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.describe(
        user="The user to kick",
        reason="The reason for the kick"
    )
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    "You cannot kick someone with an equal or higher role.",
                    discord.Color.red()
                )
            )

        try:
            await user.kick(reason=f"{interaction.user} (ID: {interaction.user.id}): {reason}")
            
            # Log the kick
            await self.log_action(
                interaction.guild,
                "Member Kicked",
                f"**User:** {user.mention} (ID: {user.id})\n**Moderator:** {interaction.user.mention}\n**Reason:** {reason}",
                discord.Color.orange()
            )
            
            await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Member Kicked",
                    f"{user.mention} has been kicked.\n**Reason:** {reason}",
                    discord.Color.green()
                )
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    f"Failed to kick user: {str(e)}",
                    discord.Color.red()
                )
            )

    @app_commands.command(name="mute", description="Mute a user")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(
        user="The user to mute",
        duration="Duration in minutes (0 for permanent)",
        reason="The reason for the mute"
    )
    async def mute(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member, 
        duration: int = 0,
        reason: str = "No reason provided"
    ):
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    "You cannot mute someone with an equal or higher role.",
                    discord.Color.red()
                )
            )

        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        muted_role_id = guild_data.get('muted_role')
        
        if not muted_role_id:
            return await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    "Muted role is not set up. Please use /setup muterole to set it up.",
                    discord.Color.red()
                )
            )
        
        muted_role = interaction.guild.get_role(muted_role_id)
        if not muted_role:
            return await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    "Muted role not found. Please set it up again.",
                    discord.Color.red()
                )
            )
        
        try:
            await user.add_roles(muted_role, reason=f"Muted by {interaction.user} (ID: {interaction.user.id}): {reason}")
            
            # Log the mute
            duration_text = f"for {duration} minutes" if duration > 0 else "permanently"
            await self.log_action(
                interaction.guild,
                "Member Muted",
                f"**User:** {user.mention} (ID: {user.id})\n**Moderator:** {interaction.user.mention}\n"
                f"**Duration:** {duration_text}\n**Reason:** {reason}",
                discord.Color.dark_orange()
            )
            
            # Schedule unmute if duration is specified
            if duration > 0:
                await interaction.response.send_message(
                    embed=await self.get_mod_embed(
                        interaction,
                        "Member Muted",
                        f"{user.mention} has been muted for {duration} minutes.\n**Reason:** {reason}",
                        discord.Color.green()
                    )
                )
                
                # Store the task for later cancellation if needed
                task = self.bot.loop.create_task(
                    self.unmute_after(interaction.guild.id, user.id, duration)
                )
                self.mute_tasks[f"{interaction.guild.id}-{user.id}"] = task
            else:
                await interaction.response.send_message(
                    embed=await self.get_mod_embed(
                        interaction,
                        "Member Muted",
                        f"{user.mention} has been muted permanently.\n**Reason:** {reason}",
                        discord.Color.green()
                    )
                )
                
        except Exception as e:
            await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    f"Failed to mute user: {str(e)}",
                    discord.Color.red()
                )
            )

    async def unmute_after(self, guild_id: int, user_id: int, minutes: int):
        await asyncio.sleep(minutes * 60)
        
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
            
        user = guild.get_member(user_id)
        if not user:
            return
            
        guild_data = self.bot.data.get(str(guild_id), {})
        muted_role_id = guild_data.get('muted_role')
        
        if not muted_role_id:
            return
            
        muted_role = guild.get_role(muted_role_id)
        if not muted_role:
            return
            
        if muted_role in user.roles:
            await user.remove_roles(muted_role, reason="Automatic unmute")
            
            # Log the unmute
            await self.log_action(
                guild,
                "Member Unmuted",
                f"**User:** {user.mention} (ID: {user.id})\n**Reason:** Automatic unmute after timeout",
                discord.Color.green()
            )
        
        # Remove the task from the tasks dictionary
        self.mute_tasks.pop(f"{guild_id}-{user_id}", None)

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(
        user="The user to warn",
        reason="The reason for the warning"
    )
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    "You cannot warn someone with an equal or higher role.",
                    discord.Color.red()
                )
            )

        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        
        # Initialize warnings data structure if it doesn't exist
        if 'warnings' not in self.bot.data[guild_id]:
            self.bot.data[guild_id]['warnings'] = {}
        
        if user_id not in self.bot.data[guild_id]['warnings']:
            self.bot.data[guild_id]['warnings'][user_id] = []
        
        # Add the warning
        warning = {
            'moderator_id': interaction.user.id,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.bot.data[guild_id]['warnings'][user_id].append(warning)
        self.bot.save_data()
        
        # Log the warning
        await self.log_action(
            interaction.guild,
            "User Warned",
            f"**User:** {user.mention} (ID: {user.id})\n**Moderator:** {interaction.user.mention}\n"
            f"**Reason:** {reason}\n**Total Warnings:** {len(self.bot.data[guild_id]['warnings'][user_id])}",
            discord.Color.gold()
        )
        
        await interaction.response.send_message(
            embed=await self.get_mod_embed(
                interaction,
                "User Warned",
                f"{user.mention} has been warned.\n**Reason:** {reason}\n"
                f"**Total Warnings:** {len(self.bot.data[guild_id]['warnings'][user_id])}",
                discord.Color.orange()
            )
        )

    @app_commands.command(name="warnings", description="View a user's warnings")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(user="The user to view warnings for")
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        
        if 'warnings' not in self.bot.data.get(guild_id, {}) or user_id not in self.bot.data[guild_id]['warnings']:
            return await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "No Warnings",
                    f"{user.mention} has no warnings.",
                    discord.Color.green()
                )
            )
        
        warnings = self.bot.data[guild_id]['warnings'][user_id]
        warnings_text = []
        
        for i, warning in enumerate(warnings, 1):
            moderator = interaction.guild.get_member(warning['moderator_id'])
            mod_name = str(moderator) if moderator else f"ID: {warning['moderator_id']}"
            timestamp = datetime.fromisoformat(warning['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            warnings_text.append(
                f"**{i}.** {warning['reason']}\n"
                f"*Moderator:* {mod_name} • {timestamp}*"
            )
        
        embed = await self.get_mod_embed(
            interaction,
            f"Warnings for {user}",
            "\n\n".join(warnings_text) if warnings_text else "No warnings found.",
            discord.Color.gold()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clearwarnings", description="Clear all warnings for a user")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(user="The user to clear warnings for")
    async def clear_warnings(self, interaction: discord.Interaction, user: discord.Member):
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        
        if 'warnings' not in self.bot.data.get(guild_id, {}) or user_id not in self.bot.data[guild_id]['warnings']:
            return await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "No Warnings",
                    f"{user.mention} has no warnings to clear.",
                    discord.Color.blue()
                )
            )
        
        warning_count = len(self.bot.data[guild_id]['warnings'][user_id])
        del self.bot.data[guild_id]['warnings'][user_id]
        self.bot.save_data()
        
        # Log the action
        await self.log_action(
            interaction.guild,
            "Warnings Cleared",
            f"**User:** {user.mention} (ID: {user.id})\n**Moderator:** {interaction.user.mention}\n"
            f"**Warnings Cleared:** {warning_count}",
            discord.Color.green()
        )
        
        await interaction.response.send_message(
            embed=await self.get_mod_embed(
                interaction,
                "Warnings Cleared",
                f"Cleared {warning_count} warning(s) for {user.mention}.",
                discord.Color.green()
            )
        )

    @app_commands.command(name="purge", description="Delete multiple messages at once")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(
        amount="Number of messages to delete (1-100)",
        user="Only delete messages from this user (optional)"
    )
    async def purge(
        self, 
        interaction: discord.Interaction, 
        amount: int,
        user: Optional[discord.Member] = None
    ):
        if amount < 1 or amount > 100:
            return await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Invalid Amount",
                    "Please provide a number between 1 and 100.",
                    discord.Color.red()
                )
            )
        
        # Defer the response since we're going to be purging messages
        await interaction.response.defer(ephemeral=True)
        
        def check(message):
            if user:
                return message.author.id == user.id
            return True
        
        try:
            deleted = await interaction.channel.purge(limit=amount, check=check)
            
            # Log the purge
            await self.log_action(
                interaction.guild,
                "Messages Purged",
                f"**Moderator:** {interaction.user.mention}\n"
                f"**Channel:** {interaction.channel.mention}\n"
                f"**Messages Deleted:** {len(deleted)}\n"
                f"**Filtered by user:** {user.mention if user else 'None'}",
                discord.Color.dark_grey()
            )
            
            await interaction.followup.send(
                embed=await self.get_mod_embed(
                    interaction,
                    "Messages Purged",
                    f"Successfully deleted {len(deleted)} message(s).",
                    discord.Color.green()
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    f"Failed to purge messages: {str(e)}",
                    discord.Color.red()
                ),
                ephemeral=True
            )

    @app_commands.command(name="lock", description="Lock a channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(channel="The channel to lock (defaults to current channel)")
    async def lock(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        channel = channel or interaction.channel
        await channel.set_permissions(interaction.guild.default_role, send_messages=False)
        
        await self.log_action(
            interaction.guild,
            "Channel Locked",
            f"**Channel:** {channel.mention}\n**Moderator:** {interaction.user.mention}",
            discord.Color.orange()
        )
        
        await interaction.response.send_message(
            embed=await self.get_mod_embed(
                interaction,
                "Channel Locked",
                f"{channel.mention} has been locked.",
                discord.Color.green()
            )
        )

    @app_commands.command(name="unlock", description="Unlock a channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(channel="The channel to unlock (defaults to current channel)")
    async def unlock(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        channel = channel or interaction.channel
        await channel.set_permissions(interaction.guild.default_role, send_messages=True)
        
        await self.log_action(
            interaction.guild,
            "Channel Unlocked",
            f"**Channel:** {channel.mention}\n**Moderator:** {interaction.user.mention}",
            discord.Color.green()
        )
        
        await interaction.response.send_message(
            embed=await self.get_mod_embed(
                interaction,
                "Channel Unlocked",
                f"{channel.mention} has been unlocked.",
                discord.Color.green()
            )
        )

    @app_commands.command(name="slowmode", description="Set channel slowmode")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(
        seconds="Slowmode delay in seconds (0 to disable)",
        channel="The channel to set slowmode for (defaults to current channel)"
    )
    async def slowmode(self, interaction: discord.Interaction, seconds: int, channel: Optional[discord.TextChannel] = None):
        channel = channel or interaction.channel
        
        if seconds < 0 or seconds > 21600:
            return await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Invalid Duration",
                    "Slowmode must be between 0 and 21600 seconds (6 hours).",
                    discord.Color.red()
                ),
                ephemeral=True
            )
        
        await channel.edit(slowmode_delay=seconds)
        
        if seconds == 0:
            message = f"Slowmode disabled in {channel.mention}"
        else:
            message = f"Slowmode set to {seconds} seconds in {channel.mention}"
        
        await self.log_action(
            interaction.guild,
            "Slowmode Updated",
            f"**Channel:** {channel.mention}\n**Moderator:** {interaction.user.mention}\n**Duration:** {seconds} seconds",
            discord.Color.blue()
        )
        
        await interaction.response.send_message(
            embed=await self.get_mod_embed(
                interaction,
                "Slowmode Updated",
                message,
                discord.Color.green()
            )
        )

    @app_commands.command(name="timeout", description="Timeout a user (Discord native timeout)")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(
        user="The user to timeout",
        duration="Duration in minutes (max 40320 = 28 days)",
        reason="The reason for the timeout"
    )
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, duration: int, reason: str = "No reason provided"):
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    "You cannot timeout someone with an equal or higher role.",
                    discord.Color.red()
                )
            )
        
        if duration < 1 or duration > 40320:
            return await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Invalid Duration",
                    "Timeout duration must be between 1 and 40320 minutes (28 days).",
                    discord.Color.red()
                ),
                ephemeral=True
            )
        
        try:
            timeout_until = discord.utils.utcnow() + timedelta(minutes=duration)
            await user.timeout(timeout_until, reason=f"{interaction.user}: {reason}")
            
            await self.log_action(
                interaction.guild,
                "Member Timed Out",
                f"**User:** {user.mention} (ID: {user.id})\n**Moderator:** {interaction.user.mention}\n**Duration:** {duration} minutes\n**Reason:** {reason}",
                discord.Color.orange()
            )
            
            await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Member Timed Out",
                    f"{user.mention} has been timed out for {duration} minutes.\n**Reason:** {reason}",
                    discord.Color.green()
                )
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=await self.get_mod_embed(
                    interaction,
                    "Error",
                    f"Failed to timeout user: {str(e)}",
                    discord.Color.red()
                )
            )

    @app_commands.command(name="nuke", description="Clone and delete a channel (removes all messages)")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(channel="The channel to nuke (defaults to current channel)")
    async def nuke(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        channel = channel or interaction.channel
        
        # Confirm action
        await interaction.response.send_message(
            f"⚠️ Are you sure you want to nuke {channel.mention}? This will delete all messages!\nReply with `yes` within 10 seconds to confirm.",
            ephemeral=True
        )
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.content.lower() == 'yes'
        
        try:
            await self.bot.wait_for('message', check=check, timeout=10.0)
        except asyncio.TimeoutError:
            return await interaction.followup.send("Nuke cancelled - timed out.", ephemeral=True)
        
        # Clone and delete channel
        try:
            position = channel.position
            new_channel = await channel.clone(reason=f"Channel nuked by {interaction.user}")
            await new_channel.edit(position=position)
            await channel.delete()
            
            await self.log_action(
                interaction.guild,
                "Channel Nuked",
                f"**Channel:** #{channel.name}\n**Moderator:** {interaction.user.mention}",
                discord.Color.red()
            )
            
            embed = discord.Embed(
                title="💣 Channel Nuked",
                description=f"This channel was nuked by {interaction.user.mention}",
                color=discord.Color.green()
            )
            await new_channel.send(embed=embed, delete_after=5)
        except Exception as e:
            await interaction.followup.send(f"Failed to nuke channel: {str(e)}", ephemeral=True)

    @app_commands.command(name="membercount", description="Show server member count with breakdown")
    async def membercount(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        total = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        
        embed = discord.Embed(
            title=f"📊 {guild.name} Member Count",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Total Members", value=f"```{total:,}```", inline=True)
        embed.add_field(name="Humans", value=f"```{humans:,}```", inline=True)
        embed.add_field(name="Bots", value=f"```{bots:,}```", inline=True)
        embed.add_field(name="Online", value=f"```{online:,}```", inline=True)
        embed.add_field(name="Offline", value=f"```{total - online:,}```", inline=True)
        embed.add_field(name="Percentage Online", value=f"```{(online/total*100):.1f}%```", inline=True)
        
        guild_data = self.bot.data.get(str(guild.id), {})
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        await interaction.response.send_message(embed=embed)

    async def log_action(self, guild, action: str, description: str, color: discord.Color):
        """Helper method to log moderation actions to the log channel"""
        guild_data = self.bot.data.get(str(guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return
            
        embed = discord.Embed(
            title=f"{action} | Case #{len(guild_data.get('cases', [])) + 1}",
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass  # Silently fail if we can't log the action

async def setup(bot):
    await bot.add_cog(Moderation(bot))
