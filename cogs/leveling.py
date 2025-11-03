import discord
from discord import app_commands
from discord.ext import commands
import random
import math
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional
import io

class Leveling(commands.Cog):
    """Leveling and XP system with customizable rewards"""
    
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldowns = defaultdict(datetime)  # user_id: last_xp_time
        self.load_leveling_data()
    
    def load_leveling_data(self):
        """Load or initialize leveling data"""
        if 'leveling' not in self.bot.data:
            self.bot.data['leveling'] = {}
    
    def get_guild_leveling_config(self, guild_id: int) -> dict:
        """Get leveling configuration for a guild"""
        guild_data = self.bot.data.get(str(guild_id), {})
        return guild_data.get('leveling', {
            'enabled': False,
            'xp_min': 15,
            'xp_max': 25,
            'xp_cooldown': 60,  # seconds
            'level_up_message': True,
            'level_up_channel': None,  # None = same channel
            'level_roles': {},  # level: role_id
            'ignored_channels': [],
            'xp_multiplier': 1.0,
            'announce_levelup': True
        })
    
    def save_guild_leveling_config(self, guild_id: int, config: dict):
        """Save leveling configuration"""
        guild_data = self.bot.data.get(str(guild_id), {})
        guild_data['leveling'] = config
        self.bot.data[str(guild_id)] = guild_data
        self.bot.save_data()
    
    def get_user_xp(self, guild_id: int, user_id: int) -> dict:
        """Get user XP data"""
        key = f"{guild_id}:{user_id}"
        if key not in self.bot.data['leveling']:
            self.bot.data['leveling'][key] = {
                'xp': 0,
                'level': 0,
                'messages': 0
            }
        return self.bot.data['leveling'][key]
    
    def save_user_xp(self, guild_id: int, user_id: int, data: dict):
        """Save user XP data"""
        key = f"{guild_id}:{user_id}"
        self.bot.data['leveling'][key] = data
        self.bot.save_data()
    
    def xp_to_level(self, xp: int) -> int:
        """Calculate level from XP"""
        return int(math.sqrt(xp / 100))
    
    def level_to_xp(self, level: int) -> int:
        """Calculate XP needed for level"""
        return (level ** 2) * 100
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Award XP for messages"""
        if not message.guild or message.author.bot:
            return
        
        config = self.get_guild_leveling_config(message.guild.id)
        
        if not config.get('enabled', False):
            return
        
        # Check ignored channels
        if message.channel.id in config.get('ignored_channels', []):
            return
        
        # Check cooldown
        user_key = message.author.id
        now = datetime.utcnow()
        last_xp = self.xp_cooldowns.get(user_key)
        
        cooldown = config.get('xp_cooldown', 60)
        if last_xp and (now - last_xp).total_seconds() < cooldown:
            return
        
        # Update cooldown
        self.xp_cooldowns[user_key] = now
        
        # Get user data
        user_data = self.get_user_xp(message.guild.id, message.author.id)
        old_level = user_data['level']
        
        # Award XP
        xp_min = config.get('xp_min', 15)
        xp_max = config.get('xp_max', 25)
        xp_multiplier = config.get('xp_multiplier', 1.0)
        
        xp_gain = random.randint(xp_min, xp_max) * xp_multiplier
        user_data['xp'] += int(xp_gain)
        user_data['messages'] += 1
        
        # Calculate new level
        new_level = self.xp_to_level(user_data['xp'])
        user_data['level'] = new_level
        
        # Save data
        self.save_user_xp(message.guild.id, message.author.id, user_data)
        
        # Check for level up
        if new_level > old_level:
            await self.handle_level_up(message, new_level, config)
    
    async def handle_level_up(self, message: discord.Message, new_level: int, config: dict):
        """Handle level up event"""
        # Send level up message
        if config.get('announce_levelup', True):
            # Get level up channel
            channel_id = config.get('level_up_channel')
            if channel_id:
                channel = message.guild.get_channel(channel_id)
            else:
                channel = message.channel
            
            if channel:
                guild_data = self.bot.data.get(str(message.guild.id), {})
                
                embed = discord.Embed(
                    title="🎉 Level Up!",
                    description=f"{message.author.mention} just reached **Level {new_level}**!",
                    color=discord.Color.gold()
                )
                
                # Check for role rewards
                level_roles = config.get('level_roles', {})
                if str(new_level) in level_roles:
                    role_id = level_roles[str(new_level)]
                    role = message.guild.get_role(role_id)
                    if role:
                        try:
                            await message.author.add_roles(role, reason=f"Reached level {new_level}")
                            embed.add_field(name="Role Unlocked", value=role.mention, inline=False)
                        except:
                            pass
                
                footer_icon = guild_data.get('footer_icon', '')
                footer_text = guild_data.get('footer_text', 'Synergy Bot')
                embed.set_footer(text=footer_text, icon_url=footer_icon)
                
                await channel.send(embed=embed)
    
    @app_commands.command(name="rank", description="View your or someone's rank and XP")
    @app_commands.describe(user="User to check (defaults to you)")
    async def rank(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """View rank card"""
        user = user or interaction.user
        
        if user.bot:
            return await interaction.response.send_message("Bots don't have ranks!", ephemeral=True)
        
        config = self.get_guild_leveling_config(interaction.guild.id)
        if not config.get('enabled', False):
            return await interaction.response.send_message("Leveling system is not enabled!", ephemeral=True)
        
        user_data = self.get_user_xp(interaction.guild.id, user.id)
        
        level = user_data['level']
        xp = user_data['xp']
        messages = user_data['messages']
        
        # Calculate XP for current and next level
        current_level_xp = self.level_to_xp(level)
        next_level_xp = self.level_to_xp(level + 1)
        xp_progress = xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp
        
        # Calculate rank (leaderboard position)
        all_users = []
        for key, data in self.bot.data.get('leveling', {}).items():
            if ':' in str(key) and str(key).startswith(str(interaction.guild.id)):
                all_users.append((key, data.get('xp', 0)))
        
        all_users.sort(key=lambda x: x[1], reverse=True)
        rank = next((i + 1 for i, (key, _) in enumerate(all_users) if key == f"{interaction.guild.id}:{user.id}"), 0)
        
        # Create embed
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        
        embed = discord.Embed(
            title=f"📊 Rank Card - {user.name}",
            color=discord.Color.blue()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        embed.add_field(name="Level", value=f"```{level}```", inline=True)
        embed.add_field(name="Rank", value=f"```#{rank}```", inline=True)
        embed.add_field(name="Messages", value=f"```{messages}```", inline=True)
        
        embed.add_field(
            name="XP Progress",
            value=f"```{xp_progress}/{xp_needed} XP```\n"
                  f"{'▓' * int((xp_progress / xp_needed) * 20)}{'░' * (20 - int((xp_progress / xp_needed) * 20))}",
            inline=False
        )
        
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="xpleaderboard", description="View server XP leaderboard")
    @app_commands.describe(page="Page number (10 users per page)")
    async def xp_leaderboard(self, interaction: discord.Interaction, page: int = 1):
        """View XP leaderboard"""
        config = self.get_guild_leveling_config(interaction.guild.id)
        if not config.get('enabled', False):
            return await interaction.response.send_message("Leveling system is not enabled!", ephemeral=True)
        
        # Get all users in this guild
        guild_users = []
        for key, data in self.bot.data.get('leveling', {}).items():
            if ':' in str(key) and str(key).startswith(str(interaction.guild.id)):
                user_id = int(str(key).split(':')[1])
                guild_users.append((user_id, data.get('level', 0), data.get('xp', 0), data.get('messages', 0)))
        
        # Sort by XP
        guild_users.sort(key=lambda x: x[2], reverse=True)
        
        if not guild_users:
            return await interaction.response.send_message("No users have XP yet!", ephemeral=True)
        
        # Pagination
        per_page = 10
        total_pages = math.ceil(len(guild_users) / per_page)
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_users = guild_users[start_idx:end_idx]
        
        # Create embed
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        
        embed = discord.Embed(
            title=f"🏆 XP Leaderboard - Page {page}/{total_pages}",
            color=discord.Color.gold()
        )
        
        description = []
        for i, (user_id, level, xp, messages) in enumerate(page_users, start=start_idx + 1):
            user = interaction.guild.get_member(user_id)
            if user:
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**#{i}**"
                description.append(f"{medal} {user.mention} - Level **{level}** ({xp:,} XP)")
        
        embed.description = "\n".join(description) if description else "No users found."
        
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=f"{footer_text} | Page {page}/{total_pages}", icon_url=footer_icon)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="levelconfig", description="Configure leveling system")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        enabled="Enable or disable leveling",
        xp_min="Minimum XP per message",
        xp_max="Maximum XP per message",
        announce_levelup="Announce level ups"
    )
    async def level_config(
        self,
        interaction: discord.Interaction,
        enabled: Optional[bool] = None,
        xp_min: Optional[int] = None,
        xp_max: Optional[int] = None,
        announce_levelup: Optional[bool] = None
    ):
        """Configure leveling settings"""
        config = self.get_guild_leveling_config(interaction.guild.id)
        
        if enabled is not None:
            config['enabled'] = enabled
        if xp_min is not None:
            config['xp_min'] = max(1, xp_min)
        if xp_max is not None:
            config['xp_max'] = max(1, xp_max)
        if announce_levelup is not None:
            config['announce_levelup'] = announce_levelup
        
        self.save_guild_leveling_config(interaction.guild.id, config)
        
        embed = discord.Embed(
            title="📈 Leveling Configuration",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Status", value="✅ Enabled" if config['enabled'] else "❌ Disabled", inline=True)
        embed.add_field(name="XP Range", value=f"{config['xp_min']}-{config['xp_max']}", inline=True)
        embed.add_field(name="Announce Level Ups", value="✅" if config['announce_levelup'] else "❌", inline=True)
        
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="levelrole", description="Set role rewards for levels")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        level="Level to give role at",
        role="Role to give (leave empty to remove)"
    )
    async def level_role(self, interaction: discord.Interaction, level: int, role: Optional[discord.Role] = None):
        """Configure level role rewards"""
        config = self.get_guild_leveling_config(interaction.guild.id)
        
        if 'level_roles' not in config:
            config['level_roles'] = {}
        
        if role:
            config['level_roles'][str(level)] = role.id
            self.save_guild_leveling_config(interaction.guild.id, config)
            await interaction.response.send_message(
                f"✅ Users will receive {role.mention} at level **{level}**!",
                ephemeral=True
            )
        else:
            if str(level) in config['level_roles']:
                del config['level_roles'][str(level)]
                self.save_guild_leveling_config(interaction.guild.id, config)
                await interaction.response.send_message(f"✅ Removed role reward for level **{level}**!", ephemeral=True)
            else:
                await interaction.response.send_message(f"No role reward set for level **{level}**!", ephemeral=True)
    
    @app_commands.command(name="setxp", description="Set a user's XP (admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        user="User to set XP for",
        xp="XP amount to set"
    )
    async def set_xp(self, interaction: discord.Interaction, user: discord.Member, xp: int):
        """Set user's XP"""
        if user.bot:
            return await interaction.response.send_message("Cannot set XP for bots!", ephemeral=True)
        
        user_data = self.get_user_xp(interaction.guild.id, user.id)
        user_data['xp'] = max(0, xp)
        user_data['level'] = self.xp_to_level(xp)
        
        self.save_user_xp(interaction.guild.id, user.id, user_data)
        
        await interaction.response.send_message(
            f"✅ Set {user.mention}'s XP to **{xp:,}** (Level **{user_data['level']}**)",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Leveling(bot))
