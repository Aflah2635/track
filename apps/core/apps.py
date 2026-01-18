import os
import threading
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        # Prevent running in autoreload process or management commands if possible
        # but simplest check is RUN_MAIN for dev server
        if os.environ.get('RUN_MAIN') == 'true':
            from .bot import run_discord_bot
            
            def start_bot():
                try:
                    run_discord_bot()
                except Exception as e:
                    print(f"Error running Discord bot: {e}")

            thread = threading.Thread(target=start_bot, daemon=True)
            thread.start()

