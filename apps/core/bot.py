import os
import discord
import threading
from django.conf import settings
from apps.core.models import MaintenanceState
from discord import app_commands
from asgiref.sync import sync_to_async
from datetime import datetime

def check_permissions(interaction, admin_role_id):
    # Allow server owner always
    if interaction.user.id == interaction.guild.owner_id:
        return True
        
    # Check for role
    if admin_role_id:
        role = discord.utils.get(interaction.user.roles, id=int(admin_role_id))
        if role:
            return True
    
    return False

async def get_or_create_log_channel(guild, admin_role_id):
    # 1. Check DB for existing channel ID
    try:
        maintenance_state = await sync_to_async(MaintenanceState.objects.first)()
        if maintenance_state and maintenance_state.logging_channel_id:
            channel = guild.get_channel(int(maintenance_state.logging_channel_id))
            if channel:
                return channel
    except Exception as e:
        print(f"Error checking DB for log channel: {e}")

    # 2. Check for existing channel by name
    channel_name = "maintenance-logs"
    existing_channel = discord.utils.get(guild.channels, name=channel_name)
    if existing_channel:
        # Save to DB if not saved
        await save_log_channel_id(existing_channel.id)
        return existing_channel

    # 3. Create new private channel
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }

    if admin_role_id:
        admin_role = discord.utils.get(guild.roles, id=int(admin_role_id))
        if admin_role:
             overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True)
    
    try:
        new_channel = await guild.create_text_channel(channel_name, overwrites=overwrites, reason="Maintenance Logic Logs")
        await save_log_channel_id(new_channel.id)
        return new_channel
    except Exception as e:
        print(f"Failed to create log channel: {e}")
        return None

async def save_log_channel_id(channel_id):
    def update_db():
         obj, _ = MaintenanceState.objects.get_or_create(pk=1)
         obj.logging_channel_id = str(channel_id)
         obj.save()
    await sync_to_async(update_db)()

async def log_action(guild, user, action, status_color):
    try:
        admin_role_id = os.environ.get('DISCORD_ADMIN_ROLE_ID')
        channel = await get_or_create_log_channel(guild, admin_role_id)
        if not channel:
            return

        embed = discord.Embed(title="Maintenance Action", color=status_color, timestamp=datetime.now())
        embed.add_field(name="Action", value=action, inline=False)
        embed.add_field(name="User", value=f"{user.name} ({user.id})", inline=False)
        embed.set_footer(text="System Audit Log")
        
        await channel.send(embed=embed)
    except Exception as e:
        print(f"Logging failed: {e}")

def run_discord_bot():
    # Configuration
    TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
    GUILD_ID = os.environ.get('DISCORD_GUILD_ID')
    ADMIN_ROLE_ID = os.environ.get('DISCORD_ADMIN_ROLE_ID')

    if not TOKEN:
        print('DISCORD_BOT_TOKEN environment variable not set')
        return

    # Discord Client Setup
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    @client.event
    async def on_ready():
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            tree.copy_global_to(guild=guild)
            await tree.sync(guild=guild)
            print(f'Synced commands to guild {GUILD_ID}')
        else:
                await tree.sync()
                print('Synced commands globally')
        
        print(f'Logged in as {client.user}')

    # Maintenance Group
    maintenance_group = app_commands.Group(name="maintenance", description="Maintenance control commands")

    @maintenance_group.command(name="on", description="Enable maintenance mode")
    async def maintenance_on(interaction: discord.Interaction):
        if not check_permissions(interaction, ADMIN_ROLE_ID):
            await interaction.response.send_message("❌ **Access Denied**: You do not have permission to execute this command.", ephemeral=True)
            return

        # Wrap synchronous DB call
        await sync_to_async(MaintenanceState.set_state)(True, user_id=interaction.user.id)
        await interaction.response.send_message("✅ **Maintenance mode ENABLED**", ephemeral=True)
        
        # Log
        await log_action(interaction.guild, interaction.user, "Enabled Maintenance Mode", discord.Color.red())

    @maintenance_group.command(name="off", description="Disable maintenance mode")
    async def maintenance_off(interaction: discord.Interaction):
        if not check_permissions(interaction, ADMIN_ROLE_ID):
            await interaction.response.send_message("❌ **Access Denied**: You do not have permission to execute this command.", ephemeral=True)
            return
        
        # Wrap synchronous DB call
        await sync_to_async(MaintenanceState.set_state)(False, user_id=interaction.user.id)
        await interaction.response.send_message("✅ **Maintenance mode DISABLED**", ephemeral=True)

        # Log
        await log_action(interaction.guild, interaction.user, "Disabled Maintenance Mode", discord.Color.green())

    @maintenance_group.command(name="status", description="Check current maintenance status")
    async def maintenance_status(interaction: discord.Interaction):
        # Wrap synchronous DB call
        is_active = await sync_to_async(MaintenanceState.is_active)()
        status_text = "🔴 **Maintenance Enabled**" if is_active else "🟢 **Live**"
        await interaction.response.send_message(f"Current State: {status_text}", ephemeral=True)

    tree.add_command(maintenance_group)
    if GUILD_ID:
            tree.add_command(maintenance_group, guild=discord.Object(id=GUILD_ID))

    client.run(TOKEN)
