import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

class Config(commands.Cog):
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

    @app_commands.command(name="setup", description="Setup the bot's configuration")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        log_channel="The channel where logs will be sent",
        ticket_category="The category where ticket channels will be created",
        muted_role="The role to use for muting members"
    )
    async def setup_bot(
        self,
        interaction: discord.Interaction,
        log_channel: Optional[discord.TextChannel] = None,
        ticket_category: Optional[discord.CategoryChannel] = None,
        muted_role: Optional[discord.Role] = None
    ):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.bot.data:
            self.bot.data[guild_id] = {}
        
        config = self.bot.data[guild_id]
        changes = []
        
        if log_channel:
            config['log_channel'] = log_channel.id
            changes.append(f"✅ Log channel set to {log_channel.mention}")
            
        if ticket_category:
            config['ticket_category'] = ticket_category.id
            changes.append(f"✅ Ticket category set to {ticket_category.name}")
            
        if muted_role:
            config['muted_role'] = muted_role.id
            changes.append(f"✅ Muted role set to {muted_role.mention}")
        
        if not changes:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "No Changes Made",
                    "Please provide at least one setting to configure.",
                    discord.Color.blue()
                ),
                ephemeral=True
            )
        
        self.bot.save_data()
        
        embed = await self.get_embed(
            interaction,
            "Configuration Updated",
            "\n".join(changes),
            discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="setfooter", description="Set the footer icon and/or text for embeds")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        icon_url="The URL of the image to use as footer icon (optional)",
        text="The text to display in the footer (optional)"
    )
    async def set_footer(self, interaction: discord.Interaction, icon_url: Optional[str] = None, text: Optional[str] = None):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.bot.data:
            self.bot.data[guild_id] = {}
        
        changes = []
        
        if icon_url:
            self.bot.data[guild_id]['footer_icon'] = icon_url
            changes.append(f"✅ Footer icon updated\n[View Image]({icon_url})")
        
        if text:
            self.bot.data[guild_id]['footer_text'] = text
            changes.append(f"✅ Footer text set to: `{text}`")
        
        if not changes:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "No Changes",
                    "Please provide at least an icon URL or text to update.",
                    discord.Color.orange()
                ),
                ephemeral=True
            )
        
        self.bot.save_data()
        
        embed = await self.get_embed(
            interaction,
            "Footer Updated",
            "\n".join(changes),
            discord.Color.green()
        )
        
        # Try to set the thumbnail to the new icon
        if icon_url:
            try:
                embed.set_thumbnail(url=icon_url)
            except:
                pass
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="admin_role", description="Set the admin role")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(role="The role to set as admin")
    async def set_admin_role(self, interaction: discord.Interaction, role: discord.Role):
        """Set the admin role for the server"""
        guild_id = str(interaction.guild.id)
        if guild_id not in self.bot.data:
            self.bot.data[guild_id] = {}
        
        self.bot.data[guild_id]['admin_roles'] = [role.id]
        self.bot.save_data()
        
        await interaction.response.send_message(
            embed=await self.get_embed(
                interaction,
                "Admin Role Set",
                f"✅ Successfully set {role.mention} as an admin role.",
                discord.Color.green()
            )
        )

    @app_commands.command(name="mod_role", description="Set the moderator role")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(role="The role to set as moderator")
    async def set_mod_role(self, interaction: discord.Interaction, role: discord.Role):
        """Set the moderator role for the server"""
        guild_id = str(interaction.guild.id)
        if guild_id not in self.bot.data:
            self.bot.data[guild_id] = {}
        
        if 'mod_roles' not in self.bot.data[guild_id]:
            self.bot.data[guild_id]['mod_roles'] = []
            
        if role.id not in self.bot.data[guild_id]['mod_roles']:
            self.bot.data[guild_id]['mod_roles'].append(role.id)
            self.bot.save_data()
            
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Moderator Role Added",
                    f"✅ Successfully added {role.mention} as a moderator role.",
                    discord.Color.green()
                )
            )
        else:
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Role Already Set",
                    f"⚠️ {role.mention} is already a moderator role.",
                    discord.Color.orange()
                ),
                ephemeral=True
            )

    @app_commands.command(name="support_role", description="Add a support role")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(role="The role to add as support")
    async def add_support_role(self, interaction: discord.Interaction, role: discord.Role):
        """Add a support role for the server"""
        guild_id = str(interaction.guild.id)
        if guild_id not in self.bot.data:
            self.bot.data[guild_id] = {}
        
        if 'ticket_support_roles' not in self.bot.data[guild_id]:
            self.bot.data[guild_id]['ticket_support_roles'] = []
            
        if role.id not in self.bot.data[guild_id]['ticket_support_roles']:
            self.bot.data[guild_id]['ticket_support_roles'].append(role.id)
            self.bot.save_data()
            
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Support Role Added",
                    f"✅ Successfully added {role.mention} as a support role.",
                    discord.Color.green()
                )
            )
        else:
            await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "Role Already Set",
                    f"⚠️ {role.mention} is already a support role.",
                    discord.Color.orange()
                ),
                ephemeral=True
            )

    @app_commands.command(name="config", description="View the current configuration")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def view_config(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.bot.data or not self.bot.data[guild_id]:
            return await interaction.response.send_message(
                embed=await self.get_embed(
                    interaction,
                    "No Configuration Found",
                    "This server has no configuration set up yet. Use `/setup` to get started.",
                    discord.Color.blue()
                ),
                ephemeral=True
            )
        
        config = self.bot.data[guild_id]
        description = []
        
        # General Settings
        description.append("**📋 General Settings**")
        description.append(f"• Prefix: `{config.get('prefix', '!')}`")
        
        # Logging
        log_channel = interaction.guild.get_channel(config.get('log_channel', 0))
        description.append("\n**📜 Logging**")
        description.append(f"• Log Channel: {log_channel.mention if log_channel else '❌ Not set'}")
        
        # Roles
        description.append("\n**👥 Roles**")
        
        # Muted Role
        muted_role = interaction.guild.get_role(config.get('muted_role', 0))
        description.append(f"• Muted Role: {muted_role.mention if muted_role else '❌ Not set'}")
        
        # Support Roles
        support_roles = [interaction.guild.get_role(rid) for rid in config.get('ticket_support_roles', [])]
        support_roles = [r for r in support_roles if r is not None]
        description.append(f"• Support Roles: {', '.join(r.mention for r in support_roles) if support_roles else '❌ Not set'}")
        
        # Mod Roles
        mod_roles = [interaction.guild.get_role(rid) for rid in config.get('mod_roles', [])]
        mod_roles = [r for r in mod_roles if r is not None]
        description.append(f"• Moderator Roles: {', '.join(r.mention for r in mod_roles) if mod_roles else '❌ Not set'}")
        
        # Admin Roles
        admin_roles = [interaction.guild.get_role(rid) for rid in config.get('admin_roles', [])]
        admin_roles = [r for r in admin_roles if r is not None]
        description.append(f"• Admin Roles: {', '.join(r.mention for r in admin_roles) if admin_roles else '❌ Not set'}")
        
        # Tickets
        ticket_category = interaction.guild.get_channel(config.get('ticket_category', 0))
        description.append("\n**🎫 Tickets**")
        description.append(f"• Ticket Category: {ticket_category.mention if ticket_category else '❌ Not set'}")
        
        # Economy
        description.append("\n**💰 Economy**")
        economy_enabled = config.get('economy', {}).get('enabled', False)
        description.append(f"• Economy System: {'✅ Enabled' if economy_enabled else '❌ Disabled'}")
        
        if economy_enabled:
            currency = config['economy'].get('currency', 'coins')
            description.append(f"• Currency: {currency}")
        
        embed = await self.get_embed(
            interaction,
            f"{interaction.guild.name} Configuration",
            "\n".join(description),
            discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Config(bot))
