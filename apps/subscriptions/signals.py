from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserSubscription, SubscriptionPlan, SubscriptionAuditLog
from apps.core.bot import send_discord_log
from django.utils import timezone

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_initial_subscription(sender, instance, created, **kwargs):
    if created:
        # Assign Basic plan by default
        basic_plan = SubscriptionPlan.objects.filter(name='BASIC').first()
        if basic_plan:
            UserSubscription.objects.create(
                user=instance,
                plan=basic_plan,
                status='ACTIVE',
                payment_status='PAID'  # Basic is free/paid
            )

@receiver(pre_save, sender=UserSubscription)
def capture_old_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = UserSubscription.objects.get(pk=instance.pk)
            instance._old_plan = old_instance.plan
            instance._old_status = old_instance.status
        except UserSubscription.DoesNotExist:
            instance._old_plan = None
            instance._old_status = None
    else:
        instance._old_plan = None
        instance._old_status = None

@receiver(post_save, sender=UserSubscription)
def log_subscription_changes(sender, instance, created, **kwargs):
    action = None
    old_plan = getattr(instance, '_old_plan', None)
    new_plan = instance.plan

    if created:
        action = 'CREATED'
        send_discord_log(
            title="New User Subscription",
            details={
                "User": instance.user.username,
                "Plan": new_plan.name,
                "Status": instance.status
            },
            color=0x10B981 # Emerald
        )
    elif old_plan and old_plan != new_plan:
        # Determine action type
        # Heuristic: Compare prices to guess upgrade/downgrade
        if new_plan.price > old_plan.price:
            action = 'UPGRADE'
            color = 0x8B5CF6 # Purple
        else:
            action = 'DOWNGRADE'
            color = 0xF59E0B # Amber
            
        send_discord_log(
            title=f"Subscription {action.title()}",
            details={
                "User": instance.user.username,
                "From": old_plan.name,
                "To": new_plan.name,
                "Changed By": "System/Admin" # We don't have the request user here easily
            },
            color=color
        )
    elif instance.status == 'EXPIRED' and getattr(instance, '_old_status', '') != 'EXPIRED':
        action = 'EXPIRED'
        send_discord_log(
            title="Subscription Expired",
            details={
                "User": instance.user.username,
                "Plan": instance.plan.name
            },
            color=0xEF4444 # Red
        )

    if action:
        SubscriptionAuditLog.objects.create(
            user=instance.user,
            old_plan=old_plan,
            new_plan=new_plan,
            action=action,
            metadata={
                'reason': 'Signal update', 
                'status': instance.status
            }
        )
@receiver(post_save, sender=UserSubscription)
def enforce_limits_on_signal(sender, instance, **kwargs):
    """
    Automatically enforce account limits whenever subscription is saved.
    This handles Upgrades, Downgrades, Expiry, and Admin changes.
    """
    from apps.subscriptions.utils import enforce_subscription_limits
    try:
        # Enforce limits for the user
        enforce_subscription_limits(instance.user)
    except Exception as e:
        print(f"Error enforcing limits on signal for {instance.user.username}: {e}")
