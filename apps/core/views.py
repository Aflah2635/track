from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.core.cache import cache
from apps.accounts.models import Account, AccountAccess
from apps.transactions.models import Transaction

from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/m', block=True)
def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

@login_required
def dashboard(request):
    # Fetch owned and shared accounts
    owned_accounts = Account.objects.filter(user=request.user)
    shared_account_ids = AccountAccess.objects.filter(user=request.user).values_list('account_id', flat=True)
    shared_accounts = Account.objects.filter(id__in=shared_account_ids)
    
    all_accounts = (owned_accounts | shared_accounts).distinct()
    
    # Determine active account
    account_id = request.GET.get('account')
    active_account = None
    permission_level = 'FULL' # Default for owned
    
    if account_id:
        # Verify access
        try:
            active_account = all_accounts.get(id=account_id)
            # Save to session
            request.session['active_account_id'] = active_account.id
        except Account.DoesNotExist:
            active_account = None # Or handle error
    
    # Try getting from session if not in GET params
    if not active_account and 'active_account_id' in request.session:
        try:
            active_account = all_accounts.get(id=request.session['active_account_id'])
        except Account.DoesNotExist:
            # Session account might have been deleted or access revoked
            del request.session['active_account_id']
            active_account = None

    if not active_account and all_accounts.exists():
        active_account = all_accounts.first()
        # Set default in session
        request.session['active_account_id'] = active_account.id
    
    # Calculate data based on active account
    transactions = []
    balance = 0
    can_add_transaction = False
    can_share = False
    
    # Summary metrics
    total_credit = 0
    total_debit = 0
    total_lent = 0
    total_borrowed = 0
    
    if active_account:
        # Check permissions
        if active_account.user == request.user:
            permission_level = 'FULL'
            can_add_transaction = True
            can_share = True
        else:
            # Get shared permission
            try:
                access = AccountAccess.objects.get(user=request.user, account=active_account)
                permission_level = access.level
                if permission_level in ['ADD', 'FULL']:
                    can_add_transaction = True
            except AccountAccess.DoesNotExist:
                permission_level = 'VIEW'
        
        # Get transactions
        all_txns = active_account.transactions.select_related('category', 'created_by').order_by('-timestamp')
        
        # Filtering
        query = request.GET.get('q')
        category_filter = request.GET.get('category')
        user_filter = request.GET.get('user')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        if query:
            all_txns = all_txns.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query)
            )
            
        # Check Plan Limits for Filters
        user_sub = request.user.subscription
        if user_sub.plan.name == 'BASIC':
            if user_filter or date_from or date_to:
                 messages.info(request, "Advanced filters (User, Date) are available on Plus/Pro plans.")
                 user_filter = None
                 date_from = None
                 date_to = None

        if category_filter and category_filter.isdigit():
            all_txns = all_txns.filter(category_id=category_filter)
            
        if user_filter and user_filter.isdigit() and active_account.is_shared:
            all_txns = all_txns.filter(created_by_id=user_filter)

        if date_from:
            all_txns = all_txns.filter(timestamp__date__gte=date_from)
            
        if date_to:
            all_txns = all_txns.filter(timestamp__date__lte=date_to)
            
        # Pagination
        paginator = Paginator(all_txns, 20)
        page_number = request.GET.get('page')
        transactions = paginator.get_page(page_number)
        
        balance = active_account.balance
        
        # Calculate totals (Cached)
        cache_key = f'dashboard_stats_{active_account.id}'
        stats = cache.get(cache_key)
        
        if stats is None:
            totals = active_account.transactions.values('type').annotate(total=Sum('amount'))
            stats = {
                'total_credit': 0, 'total_debit': 0, 
                'total_lent': 0, 'total_borrowed': 0
            }
            for t in totals:
                if t['type'] == 'CREDIT':
                    stats['total_credit'] = t['total']
                elif t['type'] == 'DEBIT':
                    stats['total_debit'] = t['total']
                elif t['type'] == 'LEND':
                    stats['total_lent'] = t['total']
                elif t['type'] == 'BORROW':
                    stats['total_borrowed'] = t['total']
            cache.set(cache_key, stats, 60*60*24)
            
        total_credit = stats['total_credit']
        total_debit = stats['total_debit']
        total_lent = stats['total_lent']
        total_borrowed = stats['total_borrowed']
    
    context = {
        'accounts': all_accounts,
        'active_account': active_account,
        'transactions': transactions,
        'total_balance': balance,
        'permission_level': permission_level,
        'can_add_transaction': can_add_transaction,
        'can_share': can_share,
        'total_credit': total_credit,
        'total_debit': total_debit,
        'total_lent': total_lent,
        'total_borrowed': total_borrowed,
        
        # Filters Context
        'categories': active_account.categories.all() if active_account else [],
        'account_users': active_account.shared_users.select_related('user') if active_account and active_account.is_shared else [],
        'filter_q': query if active_account and 'query' in locals() and query else '',
        'filter_category': int(category_filter) if active_account and 'category_filter' in locals() and category_filter and category_filter.isdigit() else '',
        'filter_user': int(user_filter) if active_account and 'user_filter' in locals() and user_filter and user_filter.isdigit() else '',
        'filter_date_from': date_from if active_account and 'date_from' in locals() and date_from else '',
        'filter_date_to': date_to if active_account and 'date_to' in locals() and date_to else '',
        
        # Feature Flags
        'show_analytics': request.user.subscription.plan.allow_advanced_analytics,
    }
    return render(request, 'dashboard.html', context)

from apps.subscriptions.decorators import plan_required
from django.contrib.auth.decorators import login_required

@login_required
@plan_required('allow_advanced_analytics')
def analytics_dashboard(request):
    return render(request, 'core/analytics.html', {'title': 'Advanced Analytics'})
