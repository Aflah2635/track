from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def plan_required(feature_name):
    """
    Decorator to check if the user's subscription plan allows a specific feature.
    Usage: @plan_required('allow_export')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Middleware should ideally attach this, but as a fallback:
            if not hasattr(request, 'user_plan'):
                # Fallback if middleware not running or failed
                if hasattr(request.user, 'subscription'):
                    request.user_plan = request.user.subscription.plan
                else:
                    return redirect('pricing')

            # Check feature flag on the plan
            # We check both the exact field name OR if it's a limit that is None (unlimited)
            allowed = getattr(request.user_plan, feature_name, False)
            
            if not allowed:
                feature_display = feature_name.replace('allow_', '').replace('_', ' ').title()
                messages.error(request, f"Your plan does not support {feature_display}. Please upgrade.")
                return redirect('pricing')
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
