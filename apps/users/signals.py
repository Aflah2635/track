from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from .models import LoginActivity

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
    LoginActivity.objects.create(
        user=user,
        ip_address=ip,
        user_agent=user_agent,
        status='SUCCESS'
    )

@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    # For failed logins, we might check if 'credentials' has a username 
    # and if that user exists to log it against them, 
    # but strictly speaking user_login_failed sends 'sender' as the auth backend class usually 
    # or None if no backend matched. The credentials dict has 'username'.
    
    # Check if we can find a user by the username provided
    if request:
        username = credentials.get('username')
        if username:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(username=username)
                ip = get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                LoginActivity.objects.create(
                    user=user,
                    ip_address=ip,
                    user_agent=user_agent,
                    status='FAILED'
                )
            except User.DoesNotExist:
                pass # Can't log to a non-existent user
