from django.urls import path
from .views import SecuritySettingsView, GlobalLogoutView

urlpatterns = [
    path('security/', SecuritySettingsView.as_view(), name='security_settings'),
    path('security/logout-all/', GlobalLogoutView.as_view(), name='global_logout'),
]
