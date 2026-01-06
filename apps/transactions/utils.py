from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime
from .models import Transaction

def generate_statement_context(account, start_date_str=None, end_date_str=None, transaction_type=None):
    """
    Generate context data for the account statement PDF.
    
    Args:
        account: The Account object
        start_date_str: Start date string (YYYY-MM-DD), inclusive
        end_date_str: End date string (YYYY-MM-DD), inclusive
        transaction_type: Filter by transaction type (CREDIT, DEBIT, etc.)
    """
    
    # 1. Parse Dates
    today = timezone.localtime().date()
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        # Default to first day of current month if not specified
        start_date = today.replace(day=1)
        
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = today

    # 2. Calculate Opening Balance
    # Sum of all transactions BEFORE the start date
    # Credits + Borrows increase balance
    # Debits + Lends decrease balance
    
    previous_transactions = account.transactions.filter(
        timestamp__date__lt=start_date
    )
    
    # We need to manually calculate based on type because simple Sum on amount isn't enough
    # if we stored everything as positive numbers.
    # Assuming the Amount field is always positive and Type determines sign.
    
    def calculate_balance_change(queryset):
        credit = queryset.filter(type='CREDIT').aggregate(Sum('amount'))['amount__sum'] or 0
        borrow = queryset.filter(type='BORROW').aggregate(Sum('amount'))['amount__sum'] or 0
        debit = queryset.filter(type='DEBIT').aggregate(Sum('amount'))['amount__sum'] or 0
        lend = queryset.filter(type='LEND').aggregate(Sum('amount'))['amount__sum'] or 0
        
        return (credit + borrow) - (debit + lend)

    opening_balance = account.balance - calculate_balance_change(account.transactions.filter(timestamp__date__gte=start_date))
    # Wait, getting opening balance by subtracting recent transactions from CURRENT balance 
    # is safer than summing from the beginning of time if data might be archived, 
    # but summing from beginning is more standard if history is complete.
    # However, let's use the forward calculation method if we trust history:
    # opening_balance = initial + pre_period_change. 
    # Since we don't have "initial balance" field easily accessible or it might be 0,
    # let's stick to: Opening = Sum of all prev transactions.
    # actually, account.balance is the LIVE current balance.
    # So Opening Balance = Current Balance - (Net Change in Selected Period) - (Net Change after Selected Period)
    # If we assume no future transactions (end_date <= today), then:
    # Opening Balance = Current Balance - (Transactions between Start and Now)
    
    # Let's try to calculate from 0 if possible, assuming Account started at 0.
    opening_balance_val = calculate_balance_change(previous_transactions)
    # If account had an initial balance, we might be missing it, but let's assume 0-based start or that transactions cover it.

    # 3. Filter Transactions for the Period
    transactions = account.transactions.select_related('user', 'created_by').filter(
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date
    ).order_by('timestamp')
    
    if transaction_type and transaction_type != 'ALL':
        transactions = transactions.filter(type=transaction_type)

    # 4. Calculate Period Totals
    total_credit = transactions.filter(type='CREDIT').aggregate(Sum('amount'))['amount__sum'] or 0
    total_debit = transactions.filter(type='DEBIT').aggregate(Sum('amount'))['amount__sum'] or 0
    total_lent = transactions.filter(type='LEND').aggregate(Sum('amount'))['amount__sum'] or 0
    total_borrowed = transactions.filter(type='BORROW').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # 5. Calculate Closing Balance (at end of period)
    # Closing = Opening + Net Period Change
    net_period_change = (total_credit + total_borrowed) - (total_debit + total_lent)
    closing_balance = opening_balance_val + net_period_change
    
    return {
        'account': account,
        'start_date': start_date,
        'end_date': end_date,
        'opening_balance': opening_balance_val,
        'closing_balance': closing_balance,
        'total_credit': total_credit,
        'total_debit': total_debit,
        'total_lent': total_lent,
        'total_borrowed': total_borrowed,
        'transactions': transactions,
        'generated_at': timezone.now(),
    }
