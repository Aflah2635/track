from django.db.models.signals import post_save
from django.db import models
from django.dispatch import receiver
from django.db import transaction as db_transaction
from django.contrib.auth import get_user_model
from apps.transactions.models import Transaction
from apps.core.models import MaintenanceState
from .models import Notification, Broadcast

User = get_user_model()

@receiver(post_save, sender=Broadcast)
def send_broadcast_notifications(sender, instance, created, **kwargs):
    if created and not instance.sent:
        # Avoid circular updates
        users = User.objects.all()
        notifications = [
            Notification(
                recipient=user,
                type=instance.type,
                message=instance.message
            ) for user in users
        ]
        Notification.objects.bulk_create(notifications)
        # We can mark it as sent if we want logic to prevent double sending, 
        # though created check handles the main case.
        Broadcast.objects.filter(pk=instance.pk).update(sent=True)

@receiver(post_save, sender=Transaction)
def check_transaction_triggers(sender, instance, created, **kwargs):
    if not created:
        return

    # 1. Large Transaction Trigger
    # Threshold could be in settings, hardcoded for now as per plan
    LARGE_TRANSACTION_THRESHOLD = 10000
    if instance.amount > LARGE_TRANSACTION_THRESHOLD:
        Notification.objects.create(
            recipient=instance.user,
            type='LARGE_TRANSACTION',
            message=f"A large transaction of {instance.amount} was recorded on account {instance.account.name}."
        )

    # 2. Low Balance Trigger
    # Check balance of the account associated with the transaction
    # We might need to refresh account from DB to get latest balance if it was just updated
    account = instance.account
    account.refresh_from_db()
    
    LOW_BALANCE_THRESHOLD = 100
    if account.balance < LOW_BALANCE_THRESHOLD:
        # Avoid spamming? For now, requirement says "Low balance threshold reached", 
        # simplistic implementation is fine.
        Notification.objects.create(
            recipient=instance.user,
            type='LOW_BALANCE',
            message=f"Your account {account.name} balance is low: {account.balance}."
        )

    # 3. Shared Account Activity
    # check if account has shared users
    shared_accesses = account.shared_users.all()
    if shared_accesses.exists():
        # Notify owner if transaction by other user? 
        # Or notify all shared users about activity?
        # Requirement: "Shared account activity"
        
        # Notify the owner if they didn't make the change
        if instance.user != account.user:
             Notification.objects.create(
                recipient=account.user,
                type='SHARED_ACTIVITY',
                message=f"New activity on shared account {account.name} by {instance.user.username}."
            )
            
        # Notify shared users (except the one who made the transaction)
        for access in shared_accesses:
            if access.user != instance.user:
                Notification.objects.create(
                    recipient=access.user,
                    type='SHARED_ACTIVITY',
                    message=f"New activity on shared account {account.name} by {instance.user.username}."
                )

    # 4. Budget Exceeded
    if hasattr(account, 'monthly_budget') and account.monthly_budget > 0:
        from django.utils import timezone
        import datetime
        
        # Calculate total debits for this month
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # We need to import Transaction here or avoid it if circular import (it is imported at top though)
        # Note: We are already in a signal for Transaction, so we can use Transaction model.
        # Filter for DEBIT transactions for this account in current month
        # Also include the current transaction if it's new (it is post_save so it is in DB)
        
        monthly_debits = Transaction.objects.filter(
            account=account,
            timestamp__gte=start_of_month,
            type='DEBIT'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        if monthly_debits > account.monthly_budget:
            # Check if we already sent a notification recently or just send it?
            # To avoid spamming on every transaction after budget exceeded, we might check if there is arguably an unread notification 
            # or just send one. For simplicity, we send one.
            # But maybe strictly only if THIS transaction tipped it over? 
            # Or if it's already over, remind them?
            
            # Simple approach: Check if previous total (without this one) was below budget, and now it is above.
            previous_total = monthly_debits - instance.amount
            if previous_total <= account.monthly_budget:
                 Notification.objects.create(
                    recipient=account.user,
                    type='BUDGET_EXCEEDED',
                    message=f"Alert: You have exceeded your monthly budget of {account.monthly_budget} for account {account.name}. Current spending: {monthly_debits}"
                )

@receiver(post_save, sender=MaintenanceState)
def check_maintenance_trigger(sender, instance, **kwargs):
    if instance.is_maintenance:
        # Notify all users
        # NOTE: This might be slow for many users, but fine for this scale.
        users = User.objects.all()
        notifications = []
        for user in users:
            notifications.append(Notification(
                recipient=user,
                type='MAINTENANCE',
                message="System has entered maintenance mode."
            ))
        Notification.objects.bulk_create(notifications)
