from django.urls import path
from .views import (SecuritySettingsView, GlobalLogoutView, ProfileView, 
                    ProfileUpdateView, CustomPasswordChangeView, VerifyEmailView)

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/password/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('security/', SecuritySettingsView.as_view(), name='security_settings'),
    path('security/logout-all/', GlobalLogoutView.as_view(), name='global_logout'),
    path('verify-email/<uidb64>/<token>/', VerifyEmailView.as_view(), name='verify_email'),
]
