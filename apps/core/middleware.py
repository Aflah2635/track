from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from .models import MaintenanceState

class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for admin site
        if request.path.startswith('/admin/'):
            return self.get_response(request)
            
        # Check for frozen user or force logout
        if request.user.is_authenticated:
            if request.user.is_frozen:
                logout(request)
                messages.error(request, 'Your account has been frozen by an administrator.')
                return redirect('login')
                
            if request.user.force_logout_time:
                # Compare active session time if possible, or just force logout if set
                # For simplicity, if force_logout_time is set and greater than last_login, logout.
                # Since logout updates last_login logic might be tricky without extra session tracking.
                # A simpler approach: if force_logout_time is in the future? No, it's a timestamp of WHEN to force logout.
                # If force_logout_time > last_login, it means user hasn't logged in since the force event.
                # Wait, last_login is updated on login. So if force_logout_time > last_login, the user 
                # logged in BEFORE the force logout command.
                
                if request.user.last_login and request.user.force_logout_time > request.user.last_login:
                    logout(request)
                    messages.warning(request, 'You have been logged out by an administrator.')
                    return redirect('login')

        # Check maintenance state
        if MaintenanceState.is_active():
            # Allow superusers to bypass
            if request.user.is_authenticated and request.user.is_superuser:
                pass # Allow access
            else:
                return render(request, 'maintenance.html', status=503)

        # Check read-only state
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            if MaintenanceState.is_read_only_mode():
                 # Allow superusers to bypass
                if request.user.is_authenticated and request.user.is_superuser:
                    pass
                else:
                    messages.error(request, 'System is currently in read-only mode. No changes allowed.')
                    return redirect(request.META.get('HTTP_REFERER', '/'))

        return self.get_response(request)
