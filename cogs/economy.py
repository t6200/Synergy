import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import random
from typing import Optional, Literal

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Custom cooldown mapping that works with interactions
        self.daily_cooldown = commands.CooldownMapping.from_cooldown(
            1, 86400, commands.BucketType.user  # 24 hours cooldown
        )
        self.work_cooldown = commands.CooldownMapping.from_cooldown(
            1, 3600, commands.BucketType.user  # 1 hour cooldown
        )
        self.crime_cooldown = commands.CooldownMapping.from_cooldown(
            1, 7200, commands.BucketType.user  # 2 hours cooldown
        )
        
    def _get_cooldown_bucket(self, interaction, cooldown_mapping):
        """Helper method to get cooldown bucket for interactions"""
        # Create a mock message with the author attribute that cooldown expects
        mock_ctx = type('MockContext', (), {
            'author': interaction.user,
            'guild': interaction.guild,
            'channel': interaction.channel
        })()
        return cooldown_mapping.get_bucket(mock_ctx.message)
        self.daily_bonus = 100
        self.work_min = 50
        self.work_max = 150
        self.crime_success_rate = 0.7  # 70% success rate
        self.crime_min = 10
        self.crime_max = 500
        
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
    
    def get_currency_name(self, guild_id: str) -> str:
        """Get the currency name for the guild"""
        guild_data = self.bot.data.get(str(guild_id), {})
        return guild_data.get('economy', {}).get('currency', 'coins')
    
    def get_user_balance(self, guild_id: str, user_id: int) -> int:
        """Get a user's balance"""
        guild_data = self.bot.data.get(str(guild_id), {})
        return guild_data.get('economy', {}).get(str(user_id), 0)
    
    def set_user_balance(self, guild_id: str, user_id: int, amount: int) -> None:
        """Set a user's balance"""
        guild_id_str = str(guild_id)
        if guild_id_str not in self.bot.data:
            self.bot.data[guild_id_str] = {}
        
        if 'economy' not in self.bot.data[guild_id_str]:
            self.bot.data[guild_id_str]['economy'] = {}
        
        self.bot.data[guild_id_str]['economy'][str(user_id)] = max(0, amount)  # Prevent negative balance
        self.bot.save_data()
    
    def add_money(self, guild_id: str, user_id: int, amount: int) -> int:
        """Add money to a user's balance and return the new balance"""
        current = self.get_user_balance(guild_id, user_id)
        new_balance = current + amount
        self.set_user_balance(guild_id, user_id, new_balance)
        return new_balance
    
    def remove_money(self, guild_id: str, user_id: int, amount: int) -> bool:
        """Remove money from a user's balance if they have enough"""
        current = self.get_user_balance(guild_id, user_id)
        if current < amount:
            return False
        
        self.set_user_balance(guild_id, user_id, current - amount)
        return True
    
    @app_commands.command(name="balance", description="Check your balance or another user's balance")
    @app_commands.describe(user="The user whose balance to check (defaults to you)")
    async def balance(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Check your balance or another user's balance"""
        target = user or interaction.user
        guild_id = str(interaction.guild.id)
        
        balance = self.get_user_balance(guild_id, target.id)
        currency = self.get_currency_name(guild_id)
        
        embed = await self.get_embed(
            interaction,
            f"{target.name}'s Balance",
            f"**{balance:,}** {currency}",
            discord.Color.blue()
        )
        
        embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="daily", description="Claim your daily bonus")
    async def daily(self, interaction: discord.Interaction):
        """Claim your daily bonus"""
        guild_id = str(interaction.guild.id)
        user_id = interaction.user.id
        
        # Check cooldown using the helper method
        bucket = self._get_cooldown_bucket(interaction, self.daily_cooldown)
        retry_after = bucket.update_rate_limit()
        
        if retry_after:
            # Calculate remaining time
            remaining = int(retry_after)
            hours, remainder = divmod(remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_str = []
            if hours > 0:
                time_str.append(f"{hours} hour{'s' if hours > 1 else ''}")
            if minutes > 0:
                time_str.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
            if seconds > 0 and hours == 0:  # Only show seconds if less than an hour
                time_str.append(f"{seconds} second{'s' if seconds > 1 else ''}")
            
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Daily Cooldown",
                    f"You can claim your next daily bonus in {', '.join(time_str)}.",
                    discord.Color.orange()
                ),
                ephemeral=True
            )
        
        # Give the daily bonus
        currency = self.get_currency_name(guild_id)
        new_balance = self.add_money(guild_id, user_id, self.daily_bonus)
        
        await interaction.response.send_message(
            embed=await self.get_embed(
                interaction,
                "Daily Bonus Claimed",
                f"You've claimed your daily bonus of **{self.daily_bonus:,} {currency}**!\n"
                f"Your new balance is **{new_balance:,} {currency}**.",
                discord.Color.green()
            )
        )
    
    @app_commands.command(name="work", description="Work to earn some money")
    async def work(self, interaction: discord.Interaction):
        """Work to earn some money"""
        guild_id = str(interaction.guild.id)
        user_id = interaction.user.id
        
        # Check cooldown using the helper method
        bucket = self._get_cooldown_bucket(interaction, self.work_cooldown)
        retry_after = bucket.update_rate_limit()
        
        if retry_after:
            # Calculate remaining time
            remaining = int(retry_after)
            minutes, seconds = divmod(remaining, 60)
            
            time_str = []
            if minutes > 0:
                time_str.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
            if seconds > 0:
                time_str.append(f"{seconds} second{'s' if seconds > 1 else ''}")
            
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Work Cooldown",
                    f"You're too tired to work right now. Try again in {' and '.join(time_str)}.",
                    discord.Color.orange()
                ),
                ephemeral=True
            )
        
        # Calculate earnings
        earnings = random.randint(self.work_min, self.work_max)
        currency = self.get_currency_name(guild_id)
        new_balance = self.add_money(guild_id, user_id, earnings)
        
        # Work messages
        work_messages = [
            f"You worked at a local bakery and earned **{earnings:,} {currency}**!",
            f"You did some freelance coding and earned **{earnings:,} {currency}**!",
            f"You worked as a Discord moderator and earned **{earnings:,} {currency}**!",
            f"You streamed on Twitch and earned **{earnings:,} {currency}** in donations!",
            f"You wrote a blog post and earned **{earnings:,} {currency}** from ad revenue!"
        ]
        
        await interaction.response.send_message(
            embed=await self.get_embed(
                interaction,
                "Work Complete",
                f"{random.choice(work_messages)}\n"
                f"Your new balance is **{new_balance:,} {currency}**.",
                discord.Color.green()
            )
        )
    
    @app_commands.command(name="crime", description="Commit a crime for a chance to earn money")
    async def crime(self, interaction: discord.Interaction):
        """Commit a crime for a chance to earn money"""
        guild_id = str(interaction.guild.id)
        user_id = interaction.user.id
        
        # Check cooldown
        bucket = self.crime_cooldown.get_bucket(interaction)
        retry_after = bucket.update_rate_limit()
        
        if retry_after:
            # Calculate remaining time
            remaining = int(retry_after)
            hours, remainder = divmod(remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_str = []
            if hours > 0:
                time_str.append(f"{hours} hour{'s' if hours > 1 else ''}")
            if minutes > 0:
                time_str.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
            if seconds > 0 and hours == 0:  # Only show seconds if less than an hour
                time_str.append(f"{seconds} second{'s' if seconds > 1 else ''}")
            
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Crime Cooldown",
                    f"You're laying low right now. Try again in {' and '.join(time_str)}.",
                    discord.Color.orange()
                ),
                ephemeral=True
            )
        
        # Determine if crime is successful
        success = random.random() < self.crime_success_rate
        currency = self.get_currency_name(guild_id)
        
        if success:
            # Calculate earnings
            earnings = random.randint(self.crime_min, self.crime_max)
            new_balance = self.add_money(guild_id, user_id, earnings)
            
            # Success messages
            success_messages = [
                f"You successfully pickpocketed someone and got away with **{earnings:,} {currency}**!",
                f"You hacked into a bank and stole **{earnings:,} {currency}** without getting caught!",
                f"You sold some 'rare' items and made **{earnings:,} {currency}**!",
                f"You scammed a noob out of **{earnings:,} {currency}**!"
            ]
            
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Crime Successful",
                    f"{random.choice(success_messages)}\n"
                    f"Your new balance is **{new_balance:,} {currency}**.",
                    discord.Color.green()
                )
            )
        else:
            # Calculate fine (up to 50% of the max crime reward)
            fine = random.randint(1, self.crime_max // 2)
            current_balance = self.get_user_balance(guild_id, user_id)
            
            if current_balance < fine:
                fine = current_balance
            
            if fine > 0:
                new_balance = self.remove_money(guild_id, user_id, fine) or 0
            else:
                new_balance = 0
            
            # Failure messages
            failure_messages = [
                f"You got caught trying to steal and had to pay a fine of **{fine:,} {currency}**!",
                f"Your heist went wrong and you had to bribe the police with **{fine:,} {currency}**!",
                f"You got scammed and lost **{fine:,} {currency}** in the process!"
            ]
            
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Crime Failed",
                    f"{random.choice(failure_messages)}\n"
                    f"Your new balance is **{new_balance:,} {currency}**.",
                    discord.Color.red()
                )
            )
    
    @app_commands.command(name="pay", description="Send money to another user")
    @app_commands.describe(
        user="The user to send money to",
        amount="The amount of money to send"
    )
    async def pay(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        amount: app_commands.Range[int, 1]
    ):
        """Send money to another user"""
        if user.bot:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Invalid User",
                    "You can't send money to bots!",
                    discord.Color.red()
                ),
                ephemeral=True
            )
        
        if user == interaction.user:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Invalid User",
                    "You can't send money to yourself!",
                    discord.Color.red()
                ),
                ephemeral=True
            )
        
        guild_id = str(interaction.guild.id)
        currency = self.get_currency_name(guild_id)
        
        # Check if sender has enough money
        sender_balance = self.get_user_balance(guild_id, interaction.user.id)
        if sender_balance < amount:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Insufficient Funds",
                    f"You don't have enough {currency} to send that amount.",
                    discord.Color.red()
                ),
                ephemeral=True
            )
        
        # Transfer money
        self.remove_money(guild_id, interaction.user.id, amount)
        receiver_new_balance = self.add_money(guild_id, user.id, amount)
        
        # Get updated sender balance
        sender_new_balance = self.get_user_balance(guild_id, interaction.user.id)
        
        # Send confirmation
        embed = await self.get_embed(
            interaction,
            "Payment Sent",
            f"You've sent **{amount:,} {currency}** to {user.mention}.\n"
            f"Your new balance: **{sender_new_balance:,} {currency}**",
            discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Notify the receiver
        try:
            embed = await self.get_embed(
                interaction,
                "Payment Received",
                f"You've received **{amount:,} {currency}** from {interaction.user.mention}.\n"
                f"Your new balance: **{receiver_new_balance:,} {currency}**",
                discord.Color.green()
            )
            
            await user.send(embed=embed)
        except:
            # Couldn't DM the user, that's fine
            pass
    
    @app_commands.command(name="leaderboard", description="Show the economy leaderboard")
    @app_commands.describe(page="The page number to view (10 per page)")
    async def leaderboard(self, interaction: discord.Interaction, page: int = 1):
        """Show the economy leaderboard"""
        guild_id = str(interaction.guild.id)
        guild_data = self.bot.data.get(guild_id, {})
        
        if 'economy' not in guild_data or not guild_data['economy']:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "No Economy Data",
                    "No economy data is available yet. Start earning money with `/work` or `/daily`!",
                    discord.Color.blue()
                )
            )
        
        # Get all users with a balance
        users_balances = [
            (int(user_id), balance)
            for user_id, balance in guild_data['economy'].items()
            if isinstance(balance, int) and user_id != 'currency' and user_id != 'enabled'
        ]
        
        if not users_balances:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "No Users Found",
                    "No users with a balance found. Start earning money with `/work` or `/daily`!",
                    discord.Color.blue()
                )
            )
        
        # Sort by balance (descending)
        users_balances.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate pagination
        items_per_page = 10
        total_pages = (len(users_balances) + items_per_page - 1) // items_per_page
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_data = users_balances[start_idx:end_idx]
        
        # Create leaderboard text
        currency = self.get_currency_name(guild_id)
        leaderboard_text = []
        
        for i, (user_id, balance) in enumerate(page_data, start=start_idx + 1):
            user = interaction.guild.get_member(user_id)
            username = str(user) if user else f"Unknown User ({user_id})"
            leaderboard_text.append(f"`{i}.` **{username}** - {balance:,} {currency}")
        
        # Create embed
        embed = await self.get_embed(
            interaction,
            f"{interaction.guild.name} Economy Leaderboard",
            "\n".join(leaderboard_text) if leaderboard_text else "No data available.",
            discord.Color.blue()
        )
        
        embed.set_footer(text=f"Page {page}/{total_pages} • Total users: {len(users_balances)}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="setcurrency", description="Set the currency name for this server (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(currency_name="The name of the currency to use")
    async def set_currency(self, interaction: discord.Interaction, currency_name: str):
        """Set the currency name for this server"""
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.bot.data:
            self.bot.data[guild_id] = {}
        
        if 'economy' not in self.bot.data[guild_id]:
            self.bot.data[guild_id]['economy'] = {}
        
        old_currency = self.bot.data[guild_id]['economy'].get('currency', 'coins')
        self.bot.data[guild_id]['economy']['currency'] = currency_name
        self.bot.save_data()
        
        await interaction.response.send_message(
            embed=await self.get_embed(
                interaction,
                "Currency Updated",
                f"The currency has been changed from `{old_currency}` to `{currency_name}`.",
                discord.Color.green()
            )
        )

    @app_commands.command(name="rob", description="Attempt to rob another user")
    @app_commands.describe(user="The user to rob")
    async def rob(self, interaction: discord.Interaction, user: discord.Member):
        """Attempt to rob another user"""
        if user.bot or user == interaction.user:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Invalid Target",
                    "You can't rob bots or yourself!",
                    discord.Color.red()
                ),
                ephemeral=True
            )
        
        guild_id = str(interaction.guild.id)
        robber_balance = self.get_user_balance(guild_id, interaction.user.id)
        target_balance = self.get_user_balance(guild_id, user.id)
        currency = self.get_currency_name(guild_id)
        
        # Check if robber has at least 100 coins
        if robber_balance < 100:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Not Enough Money",
                    f"You need at least 100 {currency} to attempt a robbery!",
                    discord.Color.red()
                ),
                ephemeral=True
            )
        
        # Check if target has money
        if target_balance < 100:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Poor Target",
                    f"{user.mention} doesn't have enough money to rob!",
                    discord.Color.orange()
                ),
                ephemeral=True
            )
        
        # 40% success rate
        success = random.random() < 0.4
        
        if success:
            # Steal 10-30% of their money
            stolen = random.randint(int(target_balance * 0.1), int(target_balance * 0.3))
            self.remove_money(guild_id, user.id, stolen)
            new_balance = self.add_money(guild_id, interaction.user.id, stolen)
            
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Robbery Successful!",
                    f"You successfully robbed **{stolen:,} {currency}** from {user.mention}!\n"
                    f"Your new balance: **{new_balance:,} {currency}**",
                    discord.Color.green()
                )
            )
        else:
            # Failed - lose 20% of your money
            fine = int(robber_balance * 0.2)
            self.remove_money(guild_id, interaction.user.id, fine)
            new_balance = self.get_user_balance(guild_id, interaction.user.id)
            
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Robbery Failed!",
                    f"You got caught and had to pay a fine of **{fine:,} {currency}**!\n"
                    f"Your new balance: **{new_balance:,} {currency}**",
                    discord.Color.red()
                )
            )

    @app_commands.command(name="coinflip", description="Flip a coin and bet money")
    @app_commands.describe(
        amount="Amount to bet",
        choice="Heads or Tails"
    )
    async def coinflip(self, interaction: discord.Interaction, amount: int, choice: str):
        """Flip a coin and bet money"""
        guild_id = str(interaction.guild.id)
        balance = self.get_user_balance(guild_id, interaction.user.id)
        currency = self.get_currency_name(guild_id)
        
        if amount < 1:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Invalid Amount",
                    "You must bet at least 1 coin!",
                    discord.Color.red()
                ),
                ephemeral=True
            )
        
        if balance < amount:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Insufficient Funds",
                    f"You don't have enough {currency}!",
                    discord.Color.red()
                ),
                ephemeral=True
            )
        
        choice = choice.lower()
        if choice not in ['heads', 'tails', 'h', 't']:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Invalid Choice",
                    "Choose either 'heads' or 'tails'!",
                    discord.Color.red()
                ),
                ephemeral=True
            )
        
        # Normalize choice
        if choice in ['h', 'heads']:
            choice = 'heads'
        else:
            choice = 'tails'
        
        result = random.choice(['heads', 'tails'])
        
        if result == choice:
            # Won - double the bet
            winnings = amount
            new_balance = self.add_money(guild_id, interaction.user.id, winnings)
            
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "You Won!",
                    f"The coin landed on **{result}**! You won **{winnings:,} {currency}**!\n"
                    f"Your new balance: **{new_balance:,} {currency}**",
                    discord.Color.green()
                )
            )
        else:
            # Lost
            self.remove_money(guild_id, interaction.user.id, amount)
            new_balance = self.get_user_balance(guild_id, interaction.user.id)
            
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "You Lost!",
                    f"The coin landed on **{result}**! You lost **{amount:,} {currency}**.\n"
                    f"Your new balance: **{new_balance:,} {currency}**",
                    discord.Color.red()
                )
            )

    @app_commands.command(name="slots", description="Play the slot machine")
    @app_commands.describe(amount="Amount to bet")
    async def slots(self, interaction: discord.Interaction, amount: int):
        """Play the slot machine"""
        guild_id = str(interaction.guild.id)
        balance = self.get_user_balance(guild_id, interaction.user.id)
        currency = self.get_currency_name(guild_id)
        
        if amount < 1:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Invalid Amount",
                    "You must bet at least 1 coin!",
                    discord.Color.red()
                ),
                ephemeral=True
            )
        
        if balance < amount:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Insufficient Funds",
                    f"You don't have enough {currency}!",
                    discord.Color.red()
                ),
                ephemeral=True
            )
        
        # Slot symbols
        symbols = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎']
        
        # Spin the slots
        result = [random.choice(symbols) for _ in range(3)]
        
        # Calculate winnings
        winnings = 0
        multiplier = 0
        
        if result[0] == result[1] == result[2]:
            # All three match
            if result[0] == '💎':
                multiplier = 10  # Jackpot!
            elif result[0] == '⭐':
                multiplier = 5
            else:
                multiplier = 3
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            # Two match
            multiplier = 1.5
        
        if multiplier > 0:
            winnings = int(amount * multiplier)
            new_balance = self.add_money(guild_id, interaction.user.id, winnings - amount)
            
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "🎰 Slot Machine",
                    f"{''.join(result)}\n\n"
                    f"**You Won!** {winnings:,} {currency} (x{multiplier})!\n"
                    f"Your new balance: **{new_balance:,} {currency}**",
                    discord.Color.green()
                )
            )
        else:
            # Lost
            self.remove_money(guild_id, interaction.user.id, amount)
            new_balance = self.get_user_balance(guild_id, interaction.user.id)
            
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "🎰 Slot Machine",
                    f"{''.join(result)}\n\n"
                    f"**You Lost!** {amount:,} {currency}\n"
                    f"Your new balance: **{new_balance:,} {currency}**",
                    discord.Color.red()
                )
            )

async def setup(bot):
    await bot.add_cog(Economy(bot))
