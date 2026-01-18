from .models import Notification

def notifications_processor(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {
            'notification_count': unread_count,
            'Notification_count': unread_count
        }
    return {}
