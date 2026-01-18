from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from .models import MaintenanceState

class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if maintenance mode is enabled
        if MaintenanceState.is_active():
            # Allow access to admin, static, and media for superusers
            # Also allow if user is staff/superuser
            if request.path.startswith(settings.STATIC_URL) or \
               request.path.startswith(settings.MEDIA_URL) or \
               request.path.startswith('/admin/') or \
               (request.user.is_authenticated and request.user.is_staff):
                pass
            else:
                return render(request, 'maintenance.html', status=503)

        response = self.get_response(request)
        return response
