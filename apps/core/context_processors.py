from apps.accounts.models import Account, AccountAccess

def active_account_processor(request):
    if not request.user.is_authenticated:
        return {}

    active_account = None
    account_id = request.GET.get('account')

    if account_id:
        try:
            # Check if user owns the account
            active_account = Account.objects.get(id=account_id, user=request.user)
        except Account.DoesNotExist:
            # Check shared access
            try:
                access = AccountAccess.objects.get(account_id=account_id, user=request.user)
                active_account = access.account
            except AccountAccess.DoesNotExist:
                pass
    
    # Fallback to first owned account if no valid account selected (optional, or leave None)
    # If we want 'sticky' behavior during session, we could check session here.
    # For now, let's just return what's in URL or nothing, to avoid overwriting view logic 
    # that might default to first account. 
    # However, if we want the Navbar to show "Dashboard" link CORRECTLY pointing to an account,
    # we need to know what the "current" account is.
    # If URL param is missing, we don't know the current account unless we duplicate the view's default logic.
    
    # Let's rely on URL param. If missing, links will be generic.
    
    return {'active_account': active_account}
