from django.core.management.base import BaseCommand
from apps.core.bot import run_discord_bot

class Command(BaseCommand):
    help = 'Runs the Discord bot for maintenance control'

    def handle(self, *args, **options):
        run_discord_bot()
