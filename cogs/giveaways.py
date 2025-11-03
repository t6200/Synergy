import discord
from discord import app_commands
from discord.ext import commands, tasks
import random
from datetime import datetime, timedelta
from typing import Optional
import asyncio

class Giveaways(commands.Cog):
    """Giveaway system with customizable prizes and duration"""
    
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()
    
    def cog_unload(self):
        self.check_giveaways.cancel()
    
    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        """Check for ended giveaways"""
        now = datetime.utcnow()
        
        for guild_id, guild_data in self.bot.data.items():
            if 'giveaways' not in guild_data:
                continue
            
            giveaways = guild_data['giveaways'].copy()
            
            for giveaway_id, giveaway in giveaways.items():
                if giveaway['status'] != 'active':
                    continue
                
                end_time = datetime.fromisoformat(giveaway['end_time'])
                
                if now >= end_time:
                    await self.end_giveaway(int(guild_id), giveaway_id)
    
    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        await self.bot.wait_until_ready()
    
    async def end_giveaway(self, guild_id: int, giveaway_id: str):
        """End a giveaway and select winners"""
        try:
            guild_data = self.bot.data.get(str(guild_id), {})
            if 'giveaways' not in guild_data or giveaway_id not in guild_data['giveaways']:
                return
            
            giveaway = guild_data['giveaways'][giveaway_id]
            giveaway['status'] = 'ended'
            
            # Get guild and channel
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            
            channel = guild.get_channel(giveaway['channel_id'])
            if not channel:
                return
            
            # Get message
            try:
                message = await channel.fetch_message(giveaway['message_id'])
            except:
                return
            
            # Get participants
            participants = giveaway.get('participants', [])
            
            if not participants:
                # No participants
                embed = discord.Embed(
                    title="🎉 Giveaway Ended",
                    description=f"**Prize:** {giveaway['prize']}\n\n"
                               f"No one participated in this giveaway! 😢",
                    color=discord.Color.red()
                )
                
                await message.edit(embed=embed)
                await channel.send("The giveaway ended but no one participated!")
                
                guild_data['giveaways'][giveaway_id] = giveaway
                self.bot.save_data()
                return
            
            # Select winners
            winners_count = min(giveaway['winners'], len(participants))
            winners = random.sample(participants, winners_count)
            
            # Update giveaway data
            giveaway['selected_winners'] = winners
            guild_data['giveaways'][giveaway_id] = giveaway
            self.bot.save_data()
            
            # Create winner list
            winner_mentions = []
            for winner_id in winners:
                member = guild.get_member(winner_id)
                if member:
                    winner_mentions.append(member.mention)
            
            # Update embed
            embed = discord.Embed(
                title="🎉 Giveaway Ended!",
                description=f"**Prize:** {giveaway['prize']}\n\n"
                           f"**Winner{'s' if len(winners) > 1 else ''}:** {', '.join(winner_mentions)}",
                color=discord.Color.gold()
            )
            
            embed.add_field(name="Participants", value=str(len(participants)), inline=True)
            embed.add_field(name="Hosted by", value=f"<@{giveaway['host_id']}>", inline=True)
            
            footer_text = guild_data.get('footer_text', 'Synergy Bot')
            footer_icon = guild_data.get('footer_icon', '')
            embed.set_footer(text=footer_text, icon_url=footer_icon)
            
            await message.edit(embed=embed)
            
            # Announce winners
            winners_text = ", ".join(winner_mentions)
            await channel.send(
                f"🎉 Congratulations {winners_text}! You won **{giveaway['prize']}**!\n"
                f"Contact <@{giveaway['host_id']}> to claim your prize."
            )
        
        except Exception as e:
            pass
    
    @app_commands.command(name="giveaway", description="Start a giveaway")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        duration="Duration (e.g., 1h, 30m, 1d)",
        winners="Number of winners",
        prize="Prize description",
        channel="Channel to host giveaway (defaults to current)"
    )
    async def start_giveaway(
        self,
        interaction: discord.Interaction,
        duration: str,
        winners: int,
        prize: str,
        channel: Optional[discord.TextChannel] = None
    ):
        """Start a new giveaway"""
        channel = channel or interaction.channel
        
        # Parse duration
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            seconds = amount * time_units.get(unit, 60)
        except:
            return await interaction.response.send_message(
                "Invalid duration format! Use: 30s, 5m, 1h, 2d",
                ephemeral=True
            )
        
        if seconds < 60:
            return await interaction.response.send_message("Duration must be at least 1 minute!", ephemeral=True)
        
        if winners < 1:
            return await interaction.response.send_message("Must have at least 1 winner!", ephemeral=True)
        
        # Calculate end time
        end_time = datetime.utcnow() + timedelta(seconds=seconds)
        
        # Create embed
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"**Prize:** {prize}\n\n"
                       f"React with 🎉 to enter!\n"
                       f"**Winners:** {winners}\n"
                       f"**Ends:** <t:{int(end_time.timestamp())}:R>",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Hosted by", value=interaction.user.mention, inline=True)
        embed.add_field(name="Ends at", value=f"<t:{int(end_time.timestamp())}:F>", inline=True)
        
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        footer_icon = guild_data.get('footer_icon', '')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Send giveaway message
        await interaction.response.defer()
        message = await channel.send(embed=embed)
        await message.add_reaction("🎉")
        
        # Store giveaway data
        if 'giveaways' not in guild_data:
            guild_data['giveaways'] = {}
        
        giveaway_id = str(message.id)
        guild_data['giveaways'][giveaway_id] = {
            'message_id': message.id,
            'channel_id': channel.id,
            'host_id': interaction.user.id,
            'prize': prize,
            'winners': winners,
            'end_time': end_time.isoformat(),
            'status': 'active',
            'participants': []
        }
        
        self.bot.data[str(interaction.guild.id)] = guild_data
        self.bot.save_data()
        
        await interaction.followup.send(
            f"✅ Giveaway started in {channel.mention}!\n"
            f"**Prize:** {prize}\n"
            f"**Duration:** {duration}\n"
            f"**Winners:** {winners}",
            ephemeral=True
        )
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Track giveaway participants"""
        if payload.user_id == self.bot.user.id or not payload.guild_id:
            return
        
        if str(payload.emoji) != "🎉":
            return
        
        guild_data = self.bot.data.get(str(payload.guild_id), {})
        
        if 'giveaways' not in guild_data:
            return
        
        giveaway_id = str(payload.message_id)
        
        if giveaway_id not in guild_data['giveaways']:
            return
        
        giveaway = guild_data['giveaways'][giveaway_id]
        
        if giveaway['status'] != 'active':
            return
        
        # Add participant
        if payload.user_id not in giveaway['participants']:
            giveaway['participants'].append(payload.user_id)
            guild_data['giveaways'][giveaway_id] = giveaway
            self.bot.save_data()
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Remove participant from giveaway"""
        if payload.user_id == self.bot.user.id or not payload.guild_id:
            return
        
        if str(payload.emoji) != "🎉":
            return
        
        guild_data = self.bot.data.get(str(payload.guild_id), {})
        
        if 'giveaways' not in guild_data:
            return
        
        giveaway_id = str(payload.message_id)
        
        if giveaway_id not in guild_data['giveaways']:
            return
        
        giveaway = guild_data['giveaways'][giveaway_id]
        
        if giveaway['status'] != 'active':
            return
        
        # Remove participant
        if payload.user_id in giveaway['participants']:
            giveaway['participants'].remove(payload.user_id)
            guild_data['giveaways'][giveaway_id] = giveaway
            self.bot.save_data()
    
    @app_commands.command(name="gend", description="End a giveaway early")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(message_id="ID of the giveaway message")
    async def end_giveaway_early(self, interaction: discord.Interaction, message_id: str):
        """End a giveaway early"""
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        
        if 'giveaways' not in guild_data or message_id not in guild_data['giveaways']:
            return await interaction.response.send_message("Giveaway not found!", ephemeral=True)
        
        giveaway = guild_data['giveaways'][message_id]
        
        if giveaway['status'] != 'active':
            return await interaction.response.send_message("This giveaway has already ended!", ephemeral=True)
        
        await interaction.response.send_message("✅ Ending giveaway...", ephemeral=True)
        await self.end_giveaway(interaction.guild.id, message_id)
    
    @app_commands.command(name="greroll", description="Reroll giveaway winners")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(message_id="ID of the giveaway message")
    async def reroll_giveaway(self, interaction: discord.Interaction, message_id: str):
        """Reroll giveaway winners"""
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        
        if 'giveaways' not in guild_data or message_id not in guild_data['giveaways']:
            return await interaction.response.send_message("Giveaway not found!", ephemeral=True)
        
        giveaway = guild_data['giveaways'][message_id]
        
        if giveaway['status'] != 'ended':
            return await interaction.response.send_message("This giveaway hasn't ended yet!", ephemeral=True)
        
        participants = giveaway.get('participants', [])
        
        if not participants:
            return await interaction.response.send_message("No participants to reroll!", ephemeral=True)
        
        # Select new winners
        winners_count = min(giveaway['winners'], len(participants))
        winners = random.sample(participants, winners_count)
        
        # Update data
        giveaway['selected_winners'] = winners
        guild_data['giveaways'][message_id] = giveaway
        self.bot.save_data()
        
        # Announce new winners
        winner_mentions = []
        for winner_id in winners:
            member = interaction.guild.get_member(winner_id)
            if member:
                winner_mentions.append(member.mention)
        
        winners_text = ", ".join(winner_mentions)
        
        channel = interaction.guild.get_channel(giveaway['channel_id'])
        if channel:
            await channel.send(
                f"🎉 **REROLL!** New winner{'s' if len(winners) > 1 else ''}: {winners_text}!\n"
                f"Prize: **{giveaway['prize']}**"
            )
        
        await interaction.response.send_message(f"✅ Rerolled winners: {winners_text}", ephemeral=True)
    
    @app_commands.command(name="glist", description="List active giveaways")
    async def list_giveaways(self, interaction: discord.Interaction):
        """List all active giveaways"""
        guild_data = self.bot.data.get(str(interaction.guild.id), {})
        giveaways = guild_data.get('giveaways', {})
        
        active = [g for g in giveaways.values() if g['status'] == 'active']
        
        if not active:
            return await interaction.response.send_message("No active giveaways!", ephemeral=True)
        
        embed = discord.Embed(
            title="🎉 Active Giveaways",
            color=discord.Color.blue()
        )
        
        for giveaway in active:
            channel = interaction.guild.get_channel(giveaway['channel_id'])
            end_time = datetime.fromisoformat(giveaway['end_time'])
            
            embed.add_field(
                name=giveaway['prize'],
                value=f"**Channel:** {channel.mention if channel else 'Unknown'}\n"
                      f"**Winners:** {giveaway['winners']}\n"
                      f"**Ends:** <t:{int(end_time.timestamp())}:R>\n"
                      f"**Participants:** {len(giveaway['participants'])}",
                inline=False
            )
        
        footer_text = guild_data.get('footer_text', 'Synergy Bot')
        footer_icon = guild_data.get('footer_icon', '')
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Giveaways(bot))
