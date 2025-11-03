import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Literal

class AutoModeration(commands.Cog):
    """Auto-moderation system with anti-spam, anti-raid, and content filtering"""
    
    def __init__(self, bot):
        self.bot = bot
        self.message_cache = defaultdict(list)  # user_id: [timestamps]
        self.join_cache = defaultdict(list)  # guild_id: [timestamps]
        self.warned_users = set()
        
    def get_automod_config(self, guild_id: int) -> dict:
        """Get automod configuration for a guild"""
        guild_data = self.bot.data.get(str(guild_id), {})
        return guild_data.get('automod', {
            'enabled': False,
            'anti_spam': True,
            'anti_raid': True,
            'spam_threshold': 5,  # messages
            'spam_interval': 5,   # seconds
            'spam_action': 'mute',  # warn, mute, kick, ban
            'raid_threshold': 5,  # joins
            'raid_interval': 10,  # seconds
            'banned_words': [],
            'banned_words_action': 'delete',  # delete, warn, mute
            'mention_spam': True,
            'mention_limit': 5,
            'caps_spam': True,
            'caps_percentage': 70,
            'link_spam': False,
            'exempt_roles': [],
            'log_actions': True
        })
    
    def save_automod_config(self, guild_id: int, config: dict):
        """Save automod configuration"""
        guild_data = self.bot.data.get(str(guild_id), {})
        guild_data['automod'] = config
        self.bot.data[str(guild_id)] = guild_data
        self.bot.save_data()
    
    def is_exempt(self, member: discord.Member, config: dict) -> bool:
        """Check if member is exempt from automod"""
        if member.guild_permissions.administrator:
            return True
        
        exempt_roles = config.get('exempt_roles', [])
        return any(role.id in exempt_roles for role in member.roles)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitor messages for spam and banned content"""
        if not message.guild or message.author.bot:
            return
        
        config = self.get_automod_config(message.guild.id)
        
        if not config.get('enabled', False):
            return
        
        if self.is_exempt(message.author, config):
            return
        
        # Check banned words
        if config.get('banned_words'):
            content_lower = message.content.lower()
            for word in config['banned_words']:
                if word.lower() in content_lower:
                    await self.handle_banned_word(message, word, config)
                    return
        
        # Check mention spam
        if config.get('mention_spam', True):
            mention_limit = config.get('mention_limit', 5)
            total_mentions = len(message.mentions) + len(message.role_mentions)
            if total_mentions >= mention_limit:
                await self.handle_mention_spam(message, config)
                return
        
        # Check caps spam
        if config.get('caps_spam', True) and len(message.content) > 10:
            caps_count = sum(1 for c in message.content if c.isupper())
            caps_percentage = (caps_count / len(message.content)) * 100
            if caps_percentage >= config.get('caps_percentage', 70):
                await self.handle_caps_spam(message, config)
                return
        
        # Check link spam
        if config.get('link_spam', False):
            if 'http://' in message.content or 'https://' in message.content:
                await self.handle_link_spam(message, config)
                return
        
        # Check message spam (rate limit)
        if config.get('anti_spam', True):
            await self.check_spam(message, config)
    
    async def check_spam(self, message: discord.Message, config: dict):
        """Check for spam based on message rate"""
        user_id = message.author.id
        now = datetime.utcnow()
        
        # Add current message timestamp
        self.message_cache[user_id].append(now)
        
        # Remove old messages outside interval
        interval = config.get('spam_interval', 5)
        self.message_cache[user_id] = [
            ts for ts in self.message_cache[user_id]
            if (now - ts).total_seconds() <= interval
        ]
        
        # Check if threshold exceeded
        threshold = config.get('spam_threshold', 5)
        if len(self.message_cache[user_id]) >= threshold:
            await self.handle_spam(message, config)
            self.message_cache[user_id].clear()
    
    async def handle_spam(self, message: discord.Message, config: dict):
        """Handle spam violation"""
        action = config.get('spam_action', 'mute')
        
        try:
            # Delete recent messages
            async for msg in message.channel.history(limit=10):
                if msg.author.id == message.author.id:
                    await msg.delete()
            
            # Take action
            if action == 'warn':
                await message.channel.send(
                    f"{message.author.mention} ⚠️ Please stop spamming!",
                    delete_after=5
                )
            
            elif action == 'mute':
                muted_role = discord.utils.get(message.guild.roles, name="Muted")
                if not muted_role:
                    muted_role = await message.guild.create_role(name="Muted")
                    for channel in message.guild.channels:
                        await channel.set_permissions(muted_role, send_messages=False)
                
                await message.author.add_roles(muted_role, reason="Auto-mod: Spam detected")
                await message.channel.send(
                    f"{message.author.mention} has been muted for spamming.",
                    delete_after=10
                )
            
            elif action == 'kick':
                await message.author.kick(reason="Auto-mod: Spam detected")
                await message.channel.send(f"{message.author.mention} has been kicked for spamming.")
            
            elif action == 'ban':
                await message.author.ban(reason="Auto-mod: Spam detected", delete_message_days=1)
                await message.channel.send(f"{message.author.mention} has been banned for spamming.")
            
            # Log action
            if config.get('log_actions', True):
                await self.log_action(message.guild, "Spam Detected", message.author, action)
        
        except Exception as e:
            pass
    
    async def handle_banned_word(self, message: discord.Message, word: str, config: dict):
        """Handle banned word violation"""
        action = config.get('banned_words_action', 'delete')
        
        try:
            await message.delete()
            
            if action == 'delete':
                await message.channel.send(
                    f"{message.author.mention} ⚠️ Your message contained a banned word.",
                    delete_after=5
                )
            
            elif action == 'warn':
                await message.channel.send(
                    f"{message.author.mention} ⚠️ Warning: Do not use banned words!",
                    delete_after=5
                )
            
            elif action == 'mute':
                muted_role = discord.utils.get(message.guild.roles, name="Muted")
                if muted_role:
                    await message.author.add_roles(muted_role, reason="Auto-mod: Banned word")
                    await message.channel.send(
                        f"{message.author.mention} has been muted for using banned words.",
                        delete_after=10
                    )
            
            # Log action
            if config.get('log_actions', True):
                await self.log_action(message.guild, "Banned Word", message.author, f"Word: {word}")
        
        except Exception as e:
            pass
    
    async def handle_mention_spam(self, message: discord.Message, config: dict):
        """Handle mention spam"""
        try:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention} ⚠️ Too many mentions in one message!",
                delete_after=5
            )
            
            if config.get('log_actions', True):
                await self.log_action(message.guild, "Mention Spam", message.author, "Excessive mentions")
        except:
            pass
    
    async def handle_caps_spam(self, message: discord.Message, config: dict):
        """Handle caps spam"""
        try:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention} ⚠️ Please don't use excessive caps!",
                delete_after=5
            )
        except:
            pass
    
    async def handle_link_spam(self, message: discord.Message, config: dict):
        """Handle link spam"""
        try:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention} ⚠️ Links are not allowed in this server!",
                delete_after=5
            )
        except:
            pass
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Monitor for raid attempts"""
        config = self.get_automod_config(member.guild.id)
        
        if not config.get('enabled', False) or not config.get('anti_raid', True):
            return
        
        guild_id = member.guild.id
        now = datetime.utcnow()
        
        # Add join timestamp
        self.join_cache[guild_id].append(now)
        
        # Remove old joins outside interval
        interval = config.get('raid_interval', 10)
        self.join_cache[guild_id] = [
            ts for ts in self.join_cache[guild_id]
            if (now - ts).total_seconds() <= interval
        ]
        
        # Check if raid threshold exceeded
        threshold = config.get('raid_threshold', 5)
        if len(self.join_cache[guild_id]) >= threshold:
            await self.handle_raid(member.guild, config)
    
    async def handle_raid(self, guild: discord.Guild, config: dict):
        """Handle potential raid"""
        try:
            # Log raid attempt
            if config.get('log_actions', True):
                guild_data = self.bot.data.get(str(guild.id), {})
                log_channel_id = guild_data.get('log_channel')
                
                if log_channel_id:
                    log_channel = guild.get_channel(log_channel_id)
                    if log_channel:
                        embed = discord.Embed(
                            title="🚨 Potential Raid Detected",
                            description=f"Multiple users joined in a short time!\n"
                                       f"**Joins:** {len(self.join_cache[guild.id])} users\n"
                                       f"**Interval:** {config.get('raid_interval', 10)} seconds",
                            color=discord.Color.red(),
                            timestamp=datetime.utcnow()
                        )
                        await log_channel.send(embed=embed)
            
            # Clear cache
            self.join_cache[guild.id].clear()
        
        except Exception as e:
            pass
    
    async def log_action(self, guild: discord.Guild, action_type: str, user: discord.Member, details: str):
        """Log automod action"""
        try:
            guild_data = self.bot.data.get(str(guild.id), {})
            log_channel_id = guild_data.get('log_channel')
            
            if log_channel_id:
                log_channel = guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title=f"🤖 Auto-Mod: {action_type}",
                        color=discord.Color.orange(),
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=True)
                    embed.add_field(name="Action", value=details, inline=True)
                    
                    footer_icon = guild_data.get('footer_icon', '')
                    footer_text = guild_data.get('footer_text', 'Synergy Bot')
                    embed.set_footer(text=footer_text, icon_url=footer_icon)
                    
                    await log_channel.send(embed=embed)
        except:
            pass
    
    @app_commands.command(name="automod", description="Configure auto-moderation settings")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        enabled="Enable or disable auto-moderation",
        anti_spam="Enable anti-spam protection",
        anti_raid="Enable anti-raid protection",
        spam_action="Action to take on spam (warn/mute/kick/ban)"
    )
    async def automod_config(
        self,
        interaction: discord.Interaction,
        enabled: Optional[bool] = None,
        anti_spam: Optional[bool] = None,
        anti_raid: Optional[bool] = None,
        spam_action: Optional[Literal['warn', 'mute', 'kick', 'ban']] = None
    ):
        """Configure auto-moderation settings"""
        config = self.get_automod_config(interaction.guild.id)
        
        if enabled is not None:
            config['enabled'] = enabled
        if anti_spam is not None:
            config['anti_spam'] = anti_spam
        if anti_raid is not None:
            config['anti_raid'] = anti_raid
        if spam_action is not None:
            config['spam_action'] = spam_action
        
        self.save_automod_config(interaction.guild.id, config)
        
        embed = discord.Embed(
            title="🤖 Auto-Moderation Configuration",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Status", value="✅ Enabled" if config['enabled'] else "❌ Disabled", inline=True)
        embed.add_field(name="Anti-Spam", value="✅" if config['anti_spam'] else "❌", inline=True)
        embed.add_field(name="Anti-Raid", value="✅" if config['anti_raid'] else "❌", inline=True)
        embed.add_field(name="Spam Action", value=config['spam_action'].title(), inline=True)
        
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        footer_icon = guild_data.get('footer_icon', '')
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="bannedwords", description="Manage banned words list")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        action="Add or remove a banned word",
        word="The word to ban/unban"
    )
    async def banned_words(
        self,
        interaction: discord.Interaction,
        action: Literal['add', 'remove', 'list'],
        word: Optional[str] = None
    ):
        """Manage banned words"""
        config = self.get_automod_config(interaction.guild.id)
        
        if action == 'add' and word:
            if word.lower() not in config['banned_words']:
                config['banned_words'].append(word.lower())
                self.save_automod_config(interaction.guild.id, config)
                await interaction.response.send_message(f"✅ Added `{word}` to banned words list.", ephemeral=True)
            else:
                await interaction.response.send_message(f"⚠️ `{word}` is already banned.", ephemeral=True)
        
        elif action == 'remove' and word:
            if word.lower() in config['banned_words']:
                config['banned_words'].remove(word.lower())
                self.save_automod_config(interaction.guild.id, config)
                await interaction.response.send_message(f"✅ Removed `{word}` from banned words list.", ephemeral=True)
            else:
                await interaction.response.send_message(f"⚠️ `{word}` is not in the banned words list.", ephemeral=True)
        
        elif action == 'list':
            if config['banned_words']:
                words = ", ".join(f"`{w}`" for w in config['banned_words'])
                await interaction.response.send_message(f"**Banned Words:** {words}", ephemeral=True)
            else:
                await interaction.response.send_message("No banned words configured.", ephemeral=True)
        
        else:
            await interaction.response.send_message("Please provide a word when adding or removing.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutoModeration(bot))
