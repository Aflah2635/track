from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPE_CHOICES = [
        ('LOW_BALANCE', 'Low Balance'),
        ('BUDGET_EXCEEDED', 'Budget Exceeded'),
        ('LARGE_TRANSACTION', 'Large Transaction'),
        ('SHARED_ACTIVITY', 'Shared Activity'),
        ('MAINTENANCE', 'Maintenance'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: Link to related objects if needed for deep linking (e.g., Transaction ID)
    # Storing as string or GenericForeignKey usually, but for simplicity we can just rely on the message 
    # or add specific nullable foreign keys if strictly required. 
    # For now, message content is sufficient as per requirements.

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} - {self.recipient}"

class Broadcast(models.Model):
    message = models.TextField(help_text="Message to send to all users")
    type = models.CharField(max_length=20, choices=Notification.TYPE_CHOICES, default='MAINTENANCE')
    created_at = models.DateTimeField(auto_now_add=True)
    sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Broadcast: {self.message[:50]}..."

class EmailLog(models.Model):
    STATUS_CHOICES = [
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    email_type = models.CharField(max_length=50, help_text="e.g., VERIFICATION, PASSWORD_RESET, INVITATION")
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SENT')
    sent_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.email_type} to {self.recipient} - {self.status}"
