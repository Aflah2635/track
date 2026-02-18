from django.core.management.base import BaseCommand
from django.conf import settings
from apps.audit.utils import log_to_discord, LogEvents, LogColors
import discord
import asyncio
import os
from datetime import datetime

class Command(BaseCommand):
    help = 'Test Discord logging integration by sending sample messages.'

    def handle(self, *args, **options):
        self.stdout.write("Starting Discord Log Test...")

        TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
        GUILD_ID = os.environ.get('DISCORD_GUILD_ID')
        ADMIN_ROLE_ID = os.environ.get('DISCORD_ADMIN_ROLE_ID')

        if not TOKEN:
            self.stdout.write(self.style.ERROR("Error: DISCORD_BOT_TOKEN not found in .env"))
            return

        intents = discord.Intents.default()
        client = discord.Client(intents=intents)

        @client.event
        async def on_ready():
            self.stdout.write(f"Logged in as {client.user}")
            
            guild = None
            if GUILD_ID:
                guild = client.get_guild(int(GUILD_ID))
            
            if not guild:
                # Try to find any guild
                if client.guilds:
                    guild = client.guilds[0]
                    self.stdout.write(f"Using first available guild: {guild.name}")
                else:
                    self.stdout.write(self.style.ERROR("Bot is not in any guilds!"))
                    await client.close()
                    return

            # Helper to send log
            async def send_test_log(channel_name, title, details, color, emoji):
                channel = discord.utils.get(guild.channels, name=channel_name)
                if not channel:
                    self.stdout.write(f"Creating channel: {channel_name}...")
                    try:
                         overwrites = {
                            guild.default_role: discord.PermissionOverwrite(read_messages=False),
                            guild.me: discord.PermissionOverwrite(read_messages=True)
                        }
                         channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Failed to create channel {channel_name}: {e}"))
                        return

                embed = discord.Embed(
                    title=f"{emoji} {title}",
                    color=color,
                    timestamp=datetime.now()
                )
                for k, v in details.items():
                    embed.add_field(name=k, value=v, inline=True)
                embed.set_footer(text=f"Test Log • {channel_name}")
                
                try:
                    await channel.send(embed=embed)
                    self.stdout.write(self.style.SUCCESS(f"Sent: {title} -> {channel_name}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to send to {channel_name}: {e}"))

            # --- SEND TESTS ---
            self.stdout.write("Sending Auth Logs...")
            await send_test_log("auth-logs", "Test User Login", {"User": "TestUser", "IP": "127.0.0.1"}, LogColors.SUCCESS, "🔐")
            await send_test_log("auth-logs", "Password Changed", {"User": "TestUser", "Method": "Self Service"}, LogColors.WARNING, "🛡️")

            self.stdout.write("Sending Account Logs...")
            await send_test_log("transaction-logs", "Account Created", {"User": "TestUser", "Account": "Savings"}, LogColors.INFO, "📁")
            await send_test_log("transaction-logs", "Account Deleted", {"User": "TestUser", "Account": "Old Wallet", "Reason": "User Request"}, LogColors.ERROR, "📁")

            self.stdout.write("Sending Transaction Logs...")
            await send_test_log("transaction-logs", "Transaction Created", {"User": "TestUser", "Amount": "₹500", "Category": "Food"}, LogColors.INFO, "💰")
            await send_test_log("transaction-logs", "Data Exported", {"User": "TestUser", "Format": "CSV", "Records": "150"}, LogColors.WARNING, "📄")

            self.stdout.write("Sending Subscription Log...")
            await send_test_log("subscription-logs", "Subscription Updated", {"User": "TestUser", "Old Plan": "Basic", "New Plan": "Pro"}, LogColors.SUCCESS, "💎")

            self.stdout.write("Sending System Log...")
            await send_test_log("maintenance-logs", "Maintenance Event", {"User": "Admin", "Action": "Test"}, LogColors.WARNING, "🔧")

            self.stdout.write("All tests completed. Closing connection.")
            await client.close()

        # Run the client
        try:
            client.run(TOKEN)
        except Exception as e:
             self.stdout.write(self.style.ERROR(f"Bot failed to run: {e}"))
