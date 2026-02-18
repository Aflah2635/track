from django.db import models
from django.conf import settings
from django.utils import timezone

class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ('BASIC', 'Basic (Free)'),
        ('PLUS', 'Plus'),
        ('PRO', 'Pro'),
    ]

    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, help_text="Monthly price")
    
    # Feature Limits
    max_accounts = models.PositiveIntegerField(default=1, null=True, blank=True, help_text="Max number of accounts allowed. None for unlimited.")
    # Renamed/Aliased fields to match user request while keeping logic
    # "allow_shared_accounts" - Handled by max_shared_accounts limit
    max_shared_accounts = models.PositiveIntegerField(default=0, null=True, blank=True, help_text="Max number of shared accounts allowed. None for unlimited.")
    
    # "allow_unlimited_pdf" - Handled by pdf_export_limit (None = unlimited)
    pdf_export_limit = models.PositiveIntegerField(default=5, null=True, blank=True, help_text="Monthly PDF export limit. None means unlimited.")
    
    # Feature Flags (Renamed to 'allow_' to match request)
    allow_export = models.BooleanField(default=False, help_text="Allow exporting to CSV/Excel") # Previously can_export_csv
    allow_advanced_analytics = models.BooleanField(default=False, help_text="Access to advanced analytics") # Previously has_advanced_analytics
    
    # Extra internal flags
    has_team_collaboration = models.BooleanField(default=False, help_text="Access to team tools")
    has_basic_app_features = models.BooleanField(default=True, help_text="Basic features like adding transactions")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_name_display()

    @property
    def allow_shared_accounts(self):
        """Boolean property for frontend/logic checks if needed, but limit is authority."""
        return self.max_shared_accounts is None or self.max_shared_accounts > 0

    @property
    def allow_unlimited_pdf(self):
        return self.pdf_export_limit is None

class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CANCELED', 'Canceled'),
        ('EXPIRED', 'Expired'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    payment_status = models.CharField(max_length=20, default='PAID', help_text="Payment status (e.g., PAID, PENDING, FAILED)") # Added
    
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True) # Added Redundant with status but requested

    # For tracking usage (reset monthly)
    pdf_exports_used = models.PositiveIntegerField(default=0)
    last_usage_reset = models.DateTimeField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

    def save(self, *args, **kwargs):
        # Auto-sync is_active with status
        if self.status == 'ACTIVE':
            self.is_active = True
        else:
            self.is_active = False
        super().save(*args, **kwargs)

    def reset_usage_if_needed(self):
        now = timezone.now()
        if self.last_usage_reset.month != now.month or self.last_usage_reset.year != now.year:
            self.pdf_exports_used = 0
            self.last_usage_reset = now
            self.save()

class SubscriptionAuditLog(models.Model):
    ACTION_CHOICES = [
        ('UPGRADE', 'Upgrade'),
        ('DOWNGRADE', 'Downgrade'),
        ('EXPIRED', 'Expired'),
        ('ADMIN_CHANGE', 'Admin Change'),
        ('CREATED', 'Created'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription_logs')
    old_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_old_plans')
    new_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_new_plans')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"

    def reset_usage_if_needed(self):
        """Resets monthly usage counters if a month has passed since last reset."""
        now = timezone.now()
        # Simple check: if current month/year is different from last reset
        if now.month != self.last_usage_reset.month or now.year != self.last_usage_reset.year:
            self.pdf_exports_used = 0
            self.last_usage_reset = now
            self.save()
