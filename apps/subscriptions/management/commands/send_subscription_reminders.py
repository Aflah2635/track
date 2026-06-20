from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.subscriptions.models import UserSubscription
from apps.notifications.utils import send_tracked_email

class Command(BaseCommand):
    help = 'Sends subscription expiry reminders to users.'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        active_subscriptions = UserSubscription.objects.filter(
            status='ACTIVE',
            end_date__isnull=False
        ).select_related('user', 'plan')

        reminder_days = [7, 3, 1, 0] # 0 = expired today

        for sub in active_subscriptions:
            days_left = (sub.end_date.date() - now.date()).days
            
            if days_left in reminder_days:
                self.send_reminder(sub, days_left)
                
        self.stdout.write(self.style.SUCCESS('Successfully completed sending subscription reminders.'))

    def send_reminder(self, sub, days_left):
        subject = 'Your Subscription Is Expiring Soon'
        if days_left == 0:
            subject = 'Your Subscription Has Expired'
            
        context = {
            'user': sub.user,
            'plan': sub.plan,
            'days_left': days_left,
            'expiry_date': sub.end_date,
            # In a real app we'd construct a full absolute URI, 
            # but in a management command we don't have the request object.
            # Usually we configure a settings.SITE_URL for this.
            'renew_url': '/subscriptions/' 
        }

        send_tracked_email(
            email_type='SUBSCRIPTION_REMINDER',
            subject=subject,
            template_name='subscription_expiry',
            context=context,
            recipient_list=[sub.user.email],
            user=sub.user
        )
        self.stdout.write(f"Sent {days_left}-day reminder to {sub.user.email}")
