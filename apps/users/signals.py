from django.contrib.auth.signals import user_logged_in, user_login_failed, user_logged_out
from django.dispatch import receiver
from .models import LoginActivity
from apps.audit.utils import log_to_discord, LogEvents, LogColors

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # DB Audit
    LoginActivity.objects.create(
        user=user,
        ip_address=ip,
        user_agent=user_agent,
        status='SUCCESS'
    )
    
    # Discord Log
    log_to_discord(
        event_type=LogEvents.LOGIN,
        title="Successful Login",
        user=user,
        details={
            'IP': ip,
            'User Agent': user_agent
        },
        color=LogColors.SUCCESS
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        log_to_discord(
            event_type=LogEvents.LOGOUT,
            title="User Logged Out",
            user=user,
            color=LogColors.INFO
        )

@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get('username')
    ip = get_client_ip(request) if request else 'Unknown'
    user_agent = request.META.get('HTTP_USER_AGENT', '') if request else 'Unknown'
    
    # Try to find user
    user = None
    if username:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            pass

    # DB Audit (only if user found, to match original logic, or strictly we should log attempts too?)
    # Original logic only logged if user found. Keeping it consistent but adding Discord log for all.
    
    if user:
        LoginActivity.objects.create(
            user=user,
            ip_address=ip,
            user_agent=user_agent,
            status='FAILED'
        )
    
    # Discord Log (Warning)
    log_to_discord(
        event_type=LogEvents.LOGIN_FAILED,
        title="Failed Login Attempt",
        user=user, # might be None
        details={
            'Username Attempted': username,
            'IP': ip,
            'User Agent': user_agent
        },
        color=LogColors.WARNING
    )
