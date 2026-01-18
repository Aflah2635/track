from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal

def generate_statement_context(account, start_date_str=None, end_date_str=None, transaction_type=None, category_id=None, user_id=None):
    """
    Generate context data for the account statement PDF.
    """
    
    # 1. Parse Dates
    today = timezone.localtime().date()
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
             start_date = today.replace(day=1)
    else:
        start_date = today.replace(day=1)
        
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            end_date = today
    else:
        end_date = today

    if start_date > end_date:
        start_date = end_date.replace(day=1)

    # 2. Calculate Opening Balance
    # Opening Balance = Sum of all transactions linked to this account BEFORE the start date
    # Formula: (Credit + Borrow) - (Debit + Lend)
    # Note: We do NOT apply type/category/user filters to the opening balance, 
    # because the balance is a running total of the ACCOUNT, not the subset.
    
    previous_transactions = account.transactions.filter(
        timestamp__date__lt=start_date
    )
    
    def calculate_net_balance(queryset):
        aggregates = queryset.aggregate(
            credit=Sum('amount', filter=Q(type='CREDIT')),
            debit=Sum('amount', filter=Q(type='DEBIT')),
            lend=Sum('amount', filter=Q(type='LEND')),
            borrow=Sum('amount', filter=Q(type='BORROW'))
        )
        
        credit = aggregates['credit'] or Decimal('0.00')
        debit = aggregates['debit'] or Decimal('0.00')
        lend = aggregates['lend'] or Decimal('0.00')
        borrow = aggregates['borrow'] or Decimal('0.00')
        
        return (credit + borrow) - (debit + lend)

    opening_balance_val = calculate_net_balance(previous_transactions)

    # 3. Filter Transactions for the Period
    transactions = account.transactions.select_related('user', 'created_by', 'category').filter(
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date
    ).order_by('timestamp')
    
    # Apply Filters
    if transaction_type and transaction_type != 'ALL':
        transactions = transactions.filter(type=transaction_type)
        
    if category_id:
        transactions = transactions.filter(category_id=category_id)
        
    if user_id:
        transactions = transactions.filter(created_by_id=user_id)

    # 4. Calculate Period Totals (based on filtered transactions)
    period_aggregates = transactions.aggregate(
        credit=Sum('amount', filter=Q(type='CREDIT')),
        debit=Sum('amount', filter=Q(type='DEBIT')),
        lend=Sum('amount', filter=Q(type='LEND')),
        borrow=Sum('amount', filter=Q(type='BORROW'))
    )
    
    total_credit = period_aggregates['credit'] or Decimal('0.00')
    total_debit = period_aggregates['debit'] or Decimal('0.00')
    total_lent = period_aggregates['lend'] or Decimal('0.00')
    total_borrowed = period_aggregates['borrow'] or Decimal('0.00')
    
    # 5. Calculate Closing Balance
    # Closing Balance = Opening Balance + Net Change from Period Transactions
    # NOTE: If filters are applied (e.g. only "Food" category), "Closing Balance" is ambiguous.
    # Usually, a statement shows the ACCOUNT'S true closing balance, but the transaction list is filtered.
    # However, to avoid confusion, if filters are applied, the "Closing Balance" might not equal the bottom line.
    # We will stick to: Closing Balance = Opening Balance (of account) + Net Change (of ALL transactions in period, ignored filters) ??
    # OR: Closing Balance = Opening + Net Change (of Filtered transactions)?
    # Standard Bank Statement: Shows ALL transactions, so Closing = Opening + Net.
    # Custom Report: Might show "Total Spent on Food".
    # Let's calculate the Net Change of the FILTERED items.
    
    net_period_change = (total_credit + total_borrowed) - (total_debit + total_lent)
    
    # If no filters are applied, this is the true closing balance.
    # If filters are applied, this is "Opening + Activity in this subset".
    # User Requirement: "Closing balance". Let's show the result of Op + Net.
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
        'filters_applied': {
            'type': transaction_type,
            'category': category_id,
            'user': user_id
        }
    }
