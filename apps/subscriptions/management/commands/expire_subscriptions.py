from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.subscriptions.models import UserSubscription, SubscriptionPlan
from django.db import transaction

class Command(BaseCommand):
    help = 'Check for expired subscriptions and downgrade them to Basic'

    def handle(self, *args, **options):
        now = timezone.now()
        # Find active subscriptions that have passed their end date and are not Basic
        expired_subs = UserSubscription.objects.filter(
            end_date__lt=now,
            status='ACTIVE'
        ).exclude(plan__name='BASIC')

        if not expired_subs.exists():
            self.stdout.write(self.style.SUCCESS('No expired subscriptions found.'))
            return

        basic_plan = SubscriptionPlan.objects.get(name='BASIC')
        count = 0

        for sub in expired_subs:
            try:
                with transaction.atomic():
                    self.stdout.write(f"Expiring subscription for {sub.user.username} (Plan: {sub.plan.name})")
                    
                    # Update subscription
                    # We set status to ACTIVE because they are now active on Basic plan
                    # But we trigger the 'EXPIRED' log via signal by detecting the change or manually?
                    # The requirement says "Downgrade to Basic".
                    
                    # To trigger our signal logic correctly for 'EXPIRED', we might need to set status='EXPIRED' 
                    # OR we just rely on the Downgrade logic.
                    # Let's set it to ACTIVE on Basic, which count as a Downgrade.
                    # But the signal looks for "status == EXPIRED" to log 'Subscription Expired'.
                    
                    # Approach:
                    # 1. Update status to EXPIRED first to trigger "Subscription Expired" log?
                    # 2. Then set to Basic and Active?
                    
                    # Simpler: Just downgrade them. The signal will catch it as a "Downgrade" (Old Plan > New Plan price).
                    # But we also want to log that it was due to expiry.
                    # Let's just do the downgrade. The user will see "Downgrade" in logs, which is true.
                    
                    sub.plan = basic_plan
                    sub.end_date = None # Basic has no end date usually, or keep it? Basic is forever.
                    sub.save()
                    
                    count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to expire {sub.user.username}: {e}"))

        self.stdout.write(self.style.SUCCESS(f'Successfully downgraded {count} expired subscriptions to Basic.'))
