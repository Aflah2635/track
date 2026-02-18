from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.subscriptions.models import UserSubscription, SubscriptionPlan
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Change a user\'s subscription plan'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user')
        parser.add_argument('plan_name', type=str, help='Name of the plan (BASIC, PLUS, PRO)')
        parser.add_argument('--days', type=int, default=30, help='Days until expiry (default: 30)')

    def handle(self, *args, **options):
        username = options['username']
        plan_name = options['plan_name'].upper()
        days = options['days']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')

        try:
            plan = SubscriptionPlan.objects.get(name=plan_name)
        except SubscriptionPlan.DoesNotExist:
            raise CommandError(f'Plan "{plan_name}" does not exist. Choices: BASIC, PLUS, PRO')

        # Get or create subscription (handle limit cases where it might be missing despite middleware fix)
        sub, created = UserSubscription.objects.get_or_create(user=user, defaults={'plan': plan})
        
        old_plan_name = sub.plan.name
        sub.plan = plan
        sub.status = 'ACTIVE'
        sub.end_date = timezone.now() + timezone.timedelta(days=days) if plan_name != 'BASIC' else None
        sub.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully changed plan for user "{username}" from {old_plan_name} to {plan_name}'))
        if sub.end_date:
            self.stdout.write(self.style.SUCCESS(f'Plan will expire on {sub.end_date.strftime("%Y-%m-%d")}'))
