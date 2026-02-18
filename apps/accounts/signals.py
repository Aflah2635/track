from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from apps.subscriptions.utils import enforce_subscription_limits

@receiver(user_logged_in)
def enforce_limits_on_login(sender, user, request, **kwargs):
    """
    Ensure subscription limits are enforced every time a user logs in.
    This acts as a self-healing mechanism for any missed expiry events.
    """
    try:
        enforce_subscription_limits(user)
    except Exception as e:
        print(f"Error enforcing limits for user {user.username} on login: {e}")
