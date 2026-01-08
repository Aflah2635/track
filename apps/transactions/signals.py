from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Sum
from django.utils import timezone
from .models import Transaction
from apps.accounts.models import Account
from apps.notifications.models import Notification
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
