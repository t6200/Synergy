import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv
import logging
from typing import Optional, Literal

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize bot with intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

class SynergyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            application_id=os.getenv('APPLICATION_ID')
        )
        self.initial_extensions = [
            'cogs.moderation',
            'cogs.economy',
            'cogs.tickets',
            'cogs.config',
            'cogs.logging',
            'cogs.utility',
            'cogs.automod',
            'cogs.welcome',
            'cogs.leveling',
            'cogs.reactionroles',
            'cogs.giveaways',
            'cogs.music'
        ]
        self.data = {}
        self.load_data()

    async def setup_hook(self):
        """Called when the bot is starting up - loads cogs and syncs commands"""
        # Load all cogs
        for ext in self.initial_extensions:
            try:
                await self.load_extension(ext)
                logger.info(f'[OK] Loaded extension: {ext}')
            except Exception as e:
                logger.error(f'[ERROR] Failed to load extension {ext}: {e}')
        
        # Sync slash commands globally
        try:
            logger.info('[SYNC] Syncing slash commands globally...')
            synced = await self.tree.sync()
            logger.info(f'[OK] Successfully synced {len(synced)} slash command(s) globally')
        except Exception as e:
            logger.error(f'[ERROR] Failed to sync commands: {e}')

    def load_data(self):
        try:
            with open('save_data.json', 'r') as f:
                self.data = json.load(f)
            logger.info('Data loaded successfully')
        except FileNotFoundError:
            self.data = {}
            logger.info('No save file found, starting with empty data')
        except json.JSONDecodeError:
            self.data = {}
            logger.error('Error loading save file, starting with empty data')

    def save_data(self):
        with open('save_data.json', 'w') as f:
            json.dump(self.data, f, indent=4)
        logger.info('Data saved successfully')

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')
        self.status_task.start()

    @tasks.loop(minutes=5)
    async def status_task(self):
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f'{len(self.guilds)} servers | /help'
            )
        )

    async def on_guild_join(self, guild):
        if str(guild.id) not in self.data:
            self.data[str(guild.id)] = {
                'prefix': '!',
                'footer_icon': str(self.user.avatar.url) if self.user.avatar else '',
                'footer_text': 'Synergy Bot',
                'mod_roles': [],
                'admin_roles': [],
                'muted_role': None,
                'log_channel': None,
                'ticket_category': None,
                'ticket_support_roles': [],
                'economy': {},
                'tickets': {}
            }
            self.save_data()
        logger.info(f'Joined new guild: {guild.name} (ID: {guild.id})')

    async def on_guild_remove(self, guild):
        if str(guild.id) in self.data:
            del self.data[str(guild.id)]
            self.save_data()
        logger.info(f'Left guild: {guild.name} (ID: {guild.id})')

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You don't have permission to use this command.",
                    color=discord.Color.red()
                )
            )
        else:
            logger.error(f'Error in command {ctx.command}: {error}')
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred: {str(error)}",
                    color=discord.Color.red()
                )
            )

def main():
    bot = SynergyBot()
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
