import discord
from apps.core.bot import send_discord_log

class LogEvents:
    # Auth
    LOGIN = "User Login"
    LOGOUT = "User Logout"
    LOGIN_FAILED = "Login Failed"
    REGISTER = "User Registration"
    
    # Account
    ACCOUNT_CREATED = "Account Created"
    ACCOUNT_SHARED = "Account Shared" # or Updated
    
    # Transaction
    TRANSACTION_CREATED = "Transaction Created"
    TRANSACTION_UPDATED = "Transaction Updated"
    TRANSACTION_DELETED = "Transaction Deleted"
    
    # System
    MAINTENANCE = "Maintenance Mode"
    SECURITY = "Security Warning"
    
    # Statement
    STATEMENT_GENERATED = "Statement Generated"
    
class LogColors:
    INFO = discord.Color.blue()
    SUCCESS = discord.Color.green()
    WARNING = discord.Color.orange()
    ERROR = discord.Color.red()

def log_to_discord(event_type, title, user, details=None, color=None, emoji="ℹ️"):
    """
    Helper to send structured logs to Discord.
    """
    if details is None:
        details = {}
        
    # Robust user stringification
    if hasattr(user, 'username'):
        # Django User
        user_str = f"{user.username} ({user.id})"
    elif hasattr(user, 'name'):
        # Discord User or similar
        user_str = f"{user.name} ({user.id})"
    elif isinstance(user, str):
        user_str = user
    else:
        user_str = "System"
    
    # Default emojis if not provided (optional enhancement, but user asked for emojis)
    if not emoji or emoji == "ℹ️":
        if "Login" in event_type or "Logout" in event_type:
            emoji = "🔐"
        elif "Transaction" in event_type:
            emoji = "💰"
        elif "Account" in event_type:
            emoji = "📁"
        elif "Security" in event_type or "Failed" in event_type:
            emoji = "🛡️"
        elif "Statement" in event_type:
            emoji = "📄"
        elif "Maintenance" in event_type:
            emoji = "🔧"
    
    # Channel Routing
    channel_name = "system-logs" # Default
    if any(x in event_type for x in [LogEvents.LOGIN, LogEvents.LOGOUT, LogEvents.LOGIN_FAILED, LogEvents.REGISTER]):
        channel_name = "auth-logs"
    elif any(x in event_type for x in [LogEvents.TRANSACTION_CREATED, LogEvents.TRANSACTION_UPDATED, LogEvents.TRANSACTION_DELETED, LogEvents.STATEMENT_GENERATED]):
        channel_name = "transaction-logs"
    elif LogEvents.ACCOUNT_SHARED in event_type or LogEvents.ACCOUNT_CREATED in event_type:
        channel_name = "transaction-logs" # Or system, but account changes feel transactional
        
    send_discord_log(
        title=f"{event_type}: {title}",
        details=details,
        user=user_str,
        color=color or LogColors.INFO,
        emoji=emoji,
        channel_name=channel_name
    )
