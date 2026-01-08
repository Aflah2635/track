from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Sum
from django.utils import timezone
from .models import Transaction
from apps.accounts.models import Account
from apps.notifications.models import Notification
from apps.audit.utils import log_to_discord, LogEvents, LogColors
from decimal import Decimal

def update_account_balance_delta(account, transaction, reverse=False):
    """
    Update the account balance by applying the transaction delta.
    """
    if not account:
        return
        
    amount = Decimal(str(transaction.amount))
    
    # Check transaction type to determine sign
    # DEBIT/LEND reduces balance (Spending/Lending out)
    # CREDIT/BORROW creates balance (Income/Borrowing in)
    if transaction.type in ['DEBIT', 'LEND']:
        amount = -amount
    
    # If reversing (e.g. deleting or pre-update), flip the sign
    if reverse:
        amount = -amount
        
    account.balance += amount
    account.save()

@receiver(pre_save, sender=Transaction)
def prepare_balance_update(sender, instance, **kwargs):
    """
    If updating an existing transaction, reverse its old effect first.
    """
    if instance.pk:
        try:
            old_instance = Transaction.objects.get(pk=instance.pk)
            # If the account is changing, we reverse on the OLD account
            # If account is same, we reverse on it.
            # We use old_instance.account which captures this correctly.
            if old_instance.account:
                update_account_balance_delta(old_instance.account, old_instance, reverse=True)
        except Transaction.DoesNotExist:
            pass

@receiver(post_save, sender=Transaction)
def update_balance_save(sender, instance, created, **kwargs):
    """
    Apply the new transaction effect.
    """
    if instance.account:
        # Refresh the account instance to ensure we have the latest balance
        # (including any reversal that happened in pre_save)
        instance.account.refresh_from_db()
        update_account_balance_delta(instance.account, instance, reverse=False)

@receiver(post_delete, sender=Transaction)
def update_balance_delete(sender, instance, **kwargs):
    """
    Reverse the transaction effect on delete.
    """
    if instance.account:
        update_account_balance_delta(instance.account, instance, reverse=True)

@receiver(post_save, sender=Transaction)
def check_budget_limit(sender, instance, created, **kwargs):
    """
    Check if the transaction causes the category to exceed its monthly budget.
    """
    category = instance.category
    if not category or category.limit == 0:
        return

    # Only consider debits/lends as spending (depending on business logic)
    # Assuming DEBIT is the main spending type.
    if instance.type not in ['DEBIT', 'LEND']:
        return

    user = instance.user
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Calculate total spent in this category for the current month
    total_spent = Transaction.objects.filter(
        user=user,
        category=category,
        timestamp__gte=start_of_month,
        type__in=['DEBIT', 'LEND']
    ).aggregate(total=Sum('amount'))['total'] or 0

    if total_spent > category.limit:
        # Check if we already sent a notification for this month to avoid spamming
        # (This is a simplified check; for production maybe check last notification date)
        # For now, we'll just send it. User might get multiple if they keep spending.
        
        message = f"Budget Alert: You have exceeded your monthly budget of ${category.limit} for {category.name}. Total spent: ${total_spent}."
        
        Notification.objects.create(
            recipient=user,
            type='BUDGET_EXCEEDED',
            message=message
        )

@receiver(post_save, sender=Transaction)
def log_transaction_save(sender, instance, created, **kwargs):
    """
    Log transaction creation and updates to Discord.
    """
    event_type = LogEvents.TRANSACTION_CREATED if created else LogEvents.TRANSACTION_UPDATED
    title = f"Transaction {'Created' if created else 'Updated'}"
    color = LogColors.SUCCESS if created else LogColors.WARNING
    
    # Try to determine who did it. 
    # If created, created_by usually has it. If updated, last_modified_by.
    # Fallback to instance.user (owner) if modifier is missing, though typically modifier is better if available.
    actor = instance.created_by if created else instance.last_modified_by
    if not actor:
        actor = instance.user # Fallback
        
    details = {
        'Title': instance.title,
        'Amount': f"{instance.amount} {instance.account.currency if hasattr(instance.account, 'currency') else ''}",
        'Type': instance.type,
        'Account': instance.account.name if instance.account else 'N/A',
        'Category': instance.category.name if instance.category else 'Uncategorized'
    }
    
    log_to_discord(
        event_type=event_type,
        title=title,
        user=actor,
        details=details,
        color=color
    )

@receiver(post_delete, sender=Transaction)
def log_transaction_delete(sender, instance, **kwargs):
    """
    Log transaction deletion to Discord.
    """
    # For delete, we might not know who did it unless we track it in the view.
    # But usually we can just properly blame the user for now or 'System'.
    
    details = {
        'Title': instance.title,
        'Amount': str(instance.amount),
        'Type': instance.type,
        'Account': instance.account.name if instance.account else 'N/A'
    }
    
    log_to_discord(
        event_type=LogEvents.TRANSACTION_DELETED,
        title="Transaction Deleted",
        user=instance.user, # Best guess context
        details=details,
        color=LogColors.ERROR
    )
