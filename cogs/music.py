import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import yt_dlp as youtube_dl
from typing import Optional
import functools

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

# FFmpeg options for yt-dlp
ffmpeg_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.requester = None

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # Take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        # Create FFmpeg options as a single string
        ffmpeg_options = [
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '5',
            '-loglevel', '0',
            '-vn',
            '-b:a', '192k',
            '-f', 'opus',
            '-ar', '48000',
            '-ac', '2'
        ]
        # Create the audio source with proper options
        ffmpeg_source = discord.FFmpegOpusAudio(
            filename,
            options='-vn',
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -loglevel 0',
            codec='libopus'
        )
        return cls(ffmpeg_source, data=data)

class MusicPlayer:
    """Music player for a guild"""
    def __init__(self, ctx_or_interaction):
        # Handle both commands.Context and discord.Interaction
        if hasattr(ctx_or_interaction, 'bot'):  # It's a Context object
            self.bot = ctx_or_interaction.bot
            self.guild = ctx_or_interaction.guild
            self.channel = ctx_or_interaction.channel
            self.cog = ctx_or_interaction.cog
        else:  # It's an Interaction object
            self.bot = ctx_or_interaction.client
            self.guild = ctx_or_interaction.guild
            self.channel = ctx_or_interaction.channel
            self.cog = self.bot.get_cog('Music')

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        self.current = None
        self.volume = 0.5
        self.loop = False
        self.loop_queue = False

        # Use self.bot instead of ctx.bot
        self.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Main player loop"""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song with timeout
                async with asyncio.timeout(300):  # 5 minutes
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self.guild)

            if not isinstance(source, YTDLSource):
                try:
                    source = await YTDLSource.from_url(source.url, loop=self.bot.loop, stream=True)
                except Exception as e:
                    await self.channel.send(f'There was an error processing your song.\n'
                                          f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            voice_client = self.guild.voice_client
            if voice_client:
                voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))

                embed = discord.Embed(
                    title="🎵 Now Playing",
                    description=f"[{source.title}]({source.data.get('webpage_url')})",
                    color=discord.Color.blue()
                )
                
                if source.thumbnail:
                    embed.set_thumbnail(url=source.thumbnail)
                
                if source.duration:
                    mins, secs = divmod(source.duration, 60)
                    embed.add_field(name="Duration", value=f"{int(mins)}:{int(secs):02d}")
                
                if source.requester:
                    embed.add_field(name="Requested by", value=source.requester.mention)
                
                embed.add_field(name="Volume", value=f"{int(self.volume * 100)}%")
                
                await self.channel.send(embed=embed)

                await self.next.wait()

                # Clean up source
                source.cleanup()
                self.current = None

                # If loop is enabled, re-add the song
                if self.loop and source:
                    await self.queue.put(source)

    def destroy(self, guild):
        """Disconnect and cleanup the player"""
        return self.bot.loop.create_task(self.cog.cleanup(guild))

class Music(commands.Cog):
    """Music commands for playing songs from YouTube and other sources"""
    
    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    def get_player(self, ctx_or_interaction):
        """Get or create a music player for a guild"""
        try:
            player = self.players[ctx_or_interaction.guild.id]
        except KeyError:
            player = MusicPlayer(ctx_or_interaction)
            self.players[ctx_or_interaction.guild.id] = player

        return player

    async def cleanup(self, guild):
        """Cleanup player"""
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    @app_commands.command(name="join", description="Join your voice channel")
    async def join(self, interaction: discord.Interaction):
        """Join the user's voice channel"""
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ You need to be in a voice channel!", ephemeral=True)

        voice_channel = interaction.user.voice.channel

        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(voice_channel)
        else:
            await voice_channel.connect()

        await interaction.response.send_message(f"✅ Connected to **{voice_channel.name}**")

    @app_commands.command(name="leave", description="Leave the voice channel")
    async def leave(self, interaction: discord.Interaction):
        """Leave the voice channel and clear the queue"""
        voice_client = interaction.guild.voice_client

        if not voice_client:
            return await interaction.response.send_message("❌ I'm not in a voice channel!", ephemeral=True)

        await self.cleanup(interaction.guild)
        await interaction.response.send_message("✅ Disconnected from voice channel")

    @app_commands.command(name="play", description="Play a song from YouTube")
    @app_commands.describe(query="Song name or URL to play")
    async def play(self, interaction: discord.Interaction, query: str):
        """Play a song"""
        await interaction.response.defer()
        
        if not interaction.user.voice:
            return await interaction.followup.send("❌ You need to be in a voice channel!", ephemeral=True)

        voice_channel = interaction.user.voice.channel
        player = self.get_player(interaction)

        # Connect to voice if not connected
        if not interaction.guild.voice_client:
            await voice_channel.connect()

        try:
            # Search for the song
            player = self.get_player(interaction)
            
            source = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
            source.requester = interaction.user

            await player.queue.put(source)

            embed = discord.Embed(
                title="✅ Added to Queue",
                description=f"[{source.title}]({source.data.get('webpage_url')})",
                color=discord.Color.green()
            )
            
            if source.thumbnail:
                embed.set_thumbnail(url=source.thumbnail)
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction):
        """Pause the current song"""
        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_playing():
            return await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)

        voice_client.pause()
        await interaction.response.send_message("⏸️ Paused the music")

    @app_commands.command(name="resume", description="Resume the paused song")
    async def resume(self, interaction: discord.Interaction):
        """Resume the paused song"""
        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_paused():
            return await interaction.response.send_message("❌ Nothing is paused!", ephemeral=True)

        voice_client.resume()
        await interaction.response.send_message("▶️ Resumed the music")

    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        """Skip the current song"""
        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_playing():
            return await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)

        voice_client.stop()
        await interaction.response.send_message("⏭️ Skipped the song")

    @app_commands.command(name="stop", description="Stop the music and clear the queue")
    async def stop(self, interaction: discord.Interaction):
        """Stop the music and clear the queue"""
        voice_client = interaction.guild.voice_client

        if not voice_client:
            return await interaction.response.send_message("❌ I'm not in a voice channel!", ephemeral=True)

        # Clear the queue
        if interaction.guild.id in self.players:
            player = self.players[interaction.guild.id]
            # Clear queue
            while not player.queue.empty():
                try:
                    player.queue.get_nowait()
                except:
                    break

        if voice_client.is_playing():
            voice_client.stop()

        await interaction.response.send_message("⏹️ Stopped the music and cleared the queue")

    @app_commands.command(name="volume", description="Change the music volume")
    @app_commands.describe(volume="Volume level (0-100)")
    async def volume(self, interaction: discord.Interaction, volume: int):
        """Change the player volume"""
        voice_client = interaction.guild.voice_client

        if not voice_client:
            return await interaction.response.send_message("❌ I'm not in a voice channel!", ephemeral=True)

        if volume < 0 or volume > 100:
            return await interaction.response.send_message("❌ Volume must be between 0 and 100!", ephemeral=True)

        if interaction.guild.id in self.players:
            player = self.players[interaction.guild.id]
            player.volume = volume / 100

            if voice_client.source:
                voice_client.source.volume = volume / 100

        await interaction.response.send_message(f"🔊 Volume set to **{volume}%**")

    @app_commands.command(name="nowplaying", description="Show the currently playing song")
    async def nowplaying(self, interaction: discord.Interaction):
        """Show information about the currently playing song"""
        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_playing():
            return await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)

        if interaction.guild.id in self.players:
            player = self.players[interaction.guild.id]
            source = player.current

            if source:
                embed = discord.Embed(
                    title="🎵 Now Playing",
                    description=f"[{source.title}]({source.data.get('webpage_url')})",
                    color=discord.Color.blue()
                )
                
                if source.thumbnail:
                    embed.set_thumbnail(url=source.thumbnail)
                
                if source.duration:
                    mins, secs = divmod(source.duration, 60)
                    embed.add_field(name="Duration", value=f"{int(mins)}:{int(secs):02d}")
                
                if source.requester:
                    embed.add_field(name="Requested by", value=source.requester.mention)
                
                embed.add_field(name="Volume", value=f"{int(player.volume * 100)}%")
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)

    @app_commands.command(name="queue", description="Show the music queue")
    async def queue_command(self, interaction: discord.Interaction):
        """Show the current music queue"""
        if interaction.guild.id not in self.players:
            return await interaction.response.send_message("❌ Nothing is in the queue!", ephemeral=True)

        player = self.players[interaction.guild.id]
        
        if player.queue.empty():
            return await interaction.response.send_message("❌ The queue is empty!", ephemeral=True)

        embed = discord.Embed(
            title="🎵 Music Queue",
            description="",
            color=discord.Color.blue()
        )

        # Get queue items (up to 10)
        queue_list = list(player.queue._queue)[:10]
        
        for i, source in enumerate(queue_list, start=1):
            embed.description += f"`{i}.` {source.title}\n"

        if len(player.queue._queue) > 10:
            embed.description += f"\n*And {len(player.queue._queue) - 10} more...*"

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="loop", description="Toggle loop for the current song")
    async def loop(self, interaction: discord.Interaction):
        """Toggle loop for the current song"""
        if interaction.guild.id not in self.players:
            return await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)

        player = self.players[interaction.guild.id]
        player.loop = not player.loop

        status = "enabled" if player.loop else "disabled"
        await interaction.response.send_message(f"🔁 Loop **{status}**")

async def setup(bot):
    await bot.add_cog(Music(bot))
