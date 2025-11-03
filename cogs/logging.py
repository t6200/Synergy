import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from typing import Optional

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    async def log_action(self, guild, title: str, description: str, color: discord.Color) -> None:
        """Log an action to the log channel"""
        guild_data = self.bot.data.get(str(guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return
            
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=discord.utils.utcnow()
        )
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass  # Silently fail if we can't log the action

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        # Ignore DMs and bot messages
        if not before.guild or before.author.bot or before.content == after.content:
            return
            
        # Get log channel
        guild_data = self.bot.data.get(str(before.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = before.guild.get_channel(log_channel_id)
        if not log_channel:
            return
        
        # Create embed
        embed = discord.Embed(
            title="Message Edited",
            description=f"**Author:** {before.author.mention} (ID: {before.author.id})\n"
                      f"**Channel:** {before.channel.mention}\n"
                      f"[Jump to Message]({before.jump_url})",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Add before and after content
        embed.add_field(
            name="Before",
            value=before.content[:1024] or "*No content*",
            inline=False
        )
        
        embed.add_field(
            name="After",
            value=after.content[:1024] or "*No content*",
            inline=False
        )
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send to log channel
        try:
            await log_channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        # Ignore DMs and bot messages
        if not message.guild or message.author.bot:
            return
            
        # Get log channel
        guild_data = self.bot.data.get(str(message.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = message.guild.get_channel(log_channel_id)
        if not log_channel:
            return
        
        # Create embed
        embed = discord.Embed(
            title="Message Deleted",
            description=f"**Author:** {message.author.mention} (ID: {message.author.id})\n"
                      f"**Channel:** {message.channel.mention}\n"
                      f"**Message ID:** `{message.id}`",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        # Add message content if available
        if message.content:
            embed.add_field(
                name="Content",
                value=message.content[:1024] or "*No content*",
                inline=False
            )
        
        # Add attachment info if any
        if message.attachments:
            attachment_list = [f"[Attachment {i+1}]({a.url})" for i, a in enumerate(message.attachments)]
            embed.add_field(
                name="Attachments",
                value="\n".join(attachment_list) or "*No attachments*",
                inline=False
            )
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send to log channel
        try:
            await log_channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Get log channel
        guild_data = self.bot.data.get(str(member.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = member.guild.get_channel(log_channel_id)
        if not log_channel:
            return
        
        # Calculate account age
        account_age = (discord.utils.utcnow() - member.created_at).days
        
        # Create embed
        embed = discord.Embed(
            title="Member Joined",
            description=f"**User:** {member.mention} (ID: {member.id})\n"
                      f"**Account Created:** {discord.utils.format_dt(member.created_at, 'R')} ({account_age} days ago)\n"
                      f"**Member Count:** {member.guild.member_count}",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        # Add user avatar
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send to log channel
        try:
            await log_channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # Get log channel
        guild_data = self.bot.data.get(str(member.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = member.guild.get_channel(log_channel_id)
        if not log_channel:
            return
        
        # Calculate join duration
        join_duration = "Unknown"
        if member.joined_at:
            join_duration = f"{discord.utils.format_dt(member.joined_at, 'R')} ({(discord.utils.utcnow() - member.joined_at).days} days)"
        
        # Get roles
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        
        # Create embed
        embed = discord.Embed(
            title="Member Left",
            description=f"**User:** {member.mention} (ID: {member.id})\n"
                      f"**Account Created:** {discord.utils.format_dt(member.created_at, 'R')}\n"
                      f"**Joined:** {join_duration}\n"
                      f"**Member Count:** {member.guild.member_count}",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        # Add roles if any
        if roles:
            embed.add_field(
                name=f"Roles ({len(roles)})",
                value=", ".join(roles) if len(", ".join(roles)) < 1024 else f"{len(roles)} roles",
                inline=False
            )
        
        # Add user avatar
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send to log channel
        try:
            await log_channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Check for role changes
        if before.roles != after.roles:
            await self.log_role_change(before, after)
        
        # Check for nickname changes
        if before.nick != after.nick:
            await self.log_nickname_change(before, after)
    
    async def log_role_change(self, before: discord.Member, after: discord.Member):
        """Log role changes"""
        guild_data = self.bot.data.get(str(before.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = before.guild.get_channel(log_channel_id)
        if not log_channel:
            return
        
        # Get role changes
        added_roles = [role for role in after.roles if role not in before.roles]
        removed_roles = [role for role in before.roles if role not in after.roles]
        
        # If no actual role changes (can happen with other member updates)
        if not added_roles and not removed_roles:
            return
        
        # Create embed
        embed = discord.Embed(
            title="Member Roles Updated",
            description=f"**User:** {after.mention} (ID: {after.id})",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Add added roles if any
        if added_roles:
            embed.add_field(
                name="✅ Roles Added",
                value="\n".join([role.mention for role in added_roles]),
                inline=False
            )
        
        # Add removed roles if any
        if removed_roles:
            embed.add_field(
                name="❌ Roles Removed",
                value="\n".join([role.mention for role in removed_roles]),
                inline=False
            )
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send to log channel
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    async def log_nickname_change(self, before: discord.Member, after: discord.Member):
        """Log nickname changes"""
        guild_data = self.bot.data.get(str(before.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = before.guild.get_channel(log_channel_id)
        if not log_channel:
            return
        
        # Create embed
        embed = discord.Embed(
            title="Member Nickname Updated",
            description=f"**User:** {after.mention} (ID: {after.id})",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Add before and after nicknames
        embed.add_field(
            name="Before",
            value=before.nick or before.name,
            inline=True
        )
        
        embed.add_field(
            name="After",
            value=after.nick or after.name,
            inline=True
        )
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send to log channel
        try:
            await log_channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        # Get log channel
        guild_data = self.bot.data.get(str(channel.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = channel.guild.get_channel(log_channel_id)
        if not log_channel or log_channel == channel:  # Don't log the log channel
            return
        
        # Get channel type
        channel_type = str(channel.type).replace('_', ' ').title()
        
        # Get category info
        category = f" in {channel.category}" if channel.category else ""
        
        # Get overwrites
        overwrites = []
        for target, overwrite in channel.overwrites.items():
            if isinstance(target, discord.Role) and target.name == "@everyone":
                continue
                
            allows = [perm for perm, value in overwrite if value is True]
            denies = [perm for perm, value in overwrite if value is False]
            
            if allows or denies:
                overwrite_text = []
                if allows:
                    overwrite_text.append(f"✅ {', '.join(allows)}")
                if denies:
                    overwrite_text.append(f"❌ {', '.join(denies)}")
                
                overwrites.append(f"**{target.name}**\n" + "\n".join(overwrite_text))
        
        # Create embed
        embed = discord.Embed(
            title=f"{channel_type} Channel Created",
            description=f"**Name:** {channel.mention}{category}\n"
                      f"**ID:** `{channel.id}`",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        # Add topic if exists
        if hasattr(channel, 'topic') and channel.topic:
            embed.add_field(
                name="Topic",
                value=channel.topic[:1024],
                inline=False
            )
        
        # Add overwrites if any
        if overwrites:
            embed.add_field(
                name="Permission Overrides",
                value="\n\n".join(overwrites)[:1024],
                inline=False
            )
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send to log channel
        try:
            await log_channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        # Get log channel
        guild_data = self.bot.data.get(str(channel.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = channel.guild.get_channel(log_channel_id)
        if not log_channel or log_channel == channel:  # Don't log the log channel
            return
        
        # Get channel type
        channel_type = str(channel.type).replace('_', ' ').title()
        
        # Create embed
        embed = discord.Embed(
            title=f"{channel_type} Channel Deleted",
            description=f"**Name:** {channel.name}\n"
                      f"**ID:** `{channel.id}`",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        # Add category if exists
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(
                name="Category",
                value=channel.category.name,
                inline=True
            )
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send to log channel
        try:
            await log_channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        # Skip if no changes
        if before.name == after.name and before.position == after.position and before.category == after.category:
            return
            
        # Get log channel
        guild_data = self.bot.data.get(str(before.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = before.guild.get_channel(log_channel_id)
        if not log_channel or log_channel == before:  # Don't log the log channel
            return
        
        # Get channel type
        channel_type = str(before.type).replace('_', ' ').title()
        
        # Check what changed
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Name:** {before.name} → {after.name}")
            
        if before.category != after.category:
            before_category = before.category.name if before.category else "None"
            after_category = after.category.name if after.category else "None"
            changes.append(f"**Category:** {before_category} → {after_category}")
        
        # If no relevant changes, return
        if not changes:
            return
        
        # Create embed
        embed = discord.Embed(
            title=f"{channel_type} Channel Updated",
            description=f"**Channel:** {after.mention}\n"
                      f"**ID:** `{after.id}`",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Add changes
        embed.add_field(
            name="Changes",
            value="\n".join(changes),
            inline=False
        )
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send to log channel
        try:
            await log_channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        # Get log channel
        guild_data = self.bot.data.get(str(role.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = role.guild.get_channel(log_channel_id)
        if not log_channel:
            return
        
        # Get role permissions
        permissions = [perm for perm, value in role.permissions if value]
        
        # Create embed
        embed = discord.Embed(
            title="Role Created",
            description=f"**Name:** {role.mention}\n"
                      f"**ID:** `{role.id}`\n"
                      f"**Color:** `{str(role.color).upper()}`\n"
                      f"**Position:** {role.position}",
            color=role.color or discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Add permissions if any
        if permissions:
            embed.add_field(
                name="Permissions",
               value=", ".join(permissions).replace("_", " ").title(),
                inline=False
            )
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send to log channel
        try:
            await log_channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        # Get log channel
        guild_data = self.bot.data.get(str(role.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = role.guild.get_channel(log_channel_id)
        if not log_channel:
            return
        
        # Create embed
        embed = discord.Embed(
            title="Role Deleted",
            description=f"**Name:** {role.name}\n"
                      f"**ID:** `{role.id}`\n"
                      f"**Color:** `{str(role.color).upper()}`\n"
                      f"**Position:** {role.position}",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send to log channel
        try:
            await log_channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        # Skip if no changes
        if before.name == after.name and before.color == after.color and before.permissions == after.permissions:
            return
            
        # Get log channel
        guild_data = self.bot.data.get(str(before.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = before.guild.get_channel(log_channel_id)
        if not log_channel:
            return
        
        # Check what changed
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Name:** {before.name} → {after.name}")
            
        if before.color != after.color:
            changes.append(f"**Color:** `{str(before.color).upper()}` → `{str(after.color).upper()}`")
        
        # Check permission changes
        added_perms = [perm for perm, value in after.permissions if value and perm not in dict(before.permissions)]
        removed_perms = [perm for perm, value in before.permissions if value and perm not in dict(after.permissions)]
        
        if added_perms:
            changes.append(f"**Added Permissions:** {', '.join(added_perms).replace('_', ' ').title()}")
            
        if removed_perms:
            changes.append(f"**Removed Permissions:** {', '.join(removed_perms).replace('_', ' ').title()}")
        
        # If no relevant changes, return
        if not changes:
            return
        
        # Create embed
        embed = discord.Embed(
            title="Role Updated",
            description=f"**Role:** {after.mention}\n"
                      f"**ID:** `{after.id}`",
            color=after.color or discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Add changes
        embed.add_field(
            name="Changes",
            value="\n".join(changes),
            inline=False
        )
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send to log channel
        try:
            await log_channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Skip if no relevant changes
        if before.channel == after.channel:
            return
            
        # Get log channel
        guild_data = self.bot.data.get(str(member.guild.id), {})
        log_channel_id = guild_data.get('log_channel')
        
        if not log_channel_id:
            return
            
        log_channel = member.guild.get_channel(log_channel_id)
        if not log_channel:
            return
        
        # User joined a voice channel
        if not before.channel and after.channel:
            embed = discord.Embed(
                title="Voice Channel Joined",
                description=f"**User:** {member.mention} (ID: {member.id})\n"
                          f"**Channel:** {after.channel.mention}",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
        
        # User left a voice channel
        elif before.channel and not after.channel:
            embed = discord.Embed(
                title="Voice Channel Left",
                description=f"**User:** {member.mention} (ID: {member.id})\n"
                          f"**Channel:** {before.channel.name}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
        
        # User moved between voice channels
        elif before.channel != after.channel:
            embed = discord.Embed(
                title="Voice Channel Moved",
                description=f"**User:** {member.mention} (ID: {member.id})\n"
                          f"**From:** {before.channel.name}\n"
                          f"**To:** {after.channel.mention}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
        
        else:
            return
        
        # Add footer
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send to log channel
        try:
            await log_channel.send(embed=embed)
        except:
            pass

async def setup(bot):
    await bot.add_cog(Logging(bot))
