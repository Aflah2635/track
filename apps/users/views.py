from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, RedirectView, TemplateView, View
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.sessions.models import Session
from .forms import CustomUserCreationForm, ProfileUpdateForm
from .models import LoginActivity

from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_form'] = ProfileUpdateForm(instance=self.request.user)
        context['password_form'] = PasswordChangeForm(self.request.user)
        return context

class ProfileUpdateView(LoginRequiredMixin, View):
    def post(self, request):
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
        else:
            return render(request, 'users/profile.html', {
                'profile_form': form,
                'password_form': PasswordChangeForm(request.user)
            })
        return redirect('profile')

class CustomPasswordChangeView(LoginRequiredMixin, View):
    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
            return render(request, 'users/profile.html', {
                'profile_form': ProfileUpdateForm(instance=request.user),
                'password_form': form
            })

@method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True), name='dispatch')
class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

class SecuritySettingsView(LoginRequiredMixin, ListView):
    model = LoginActivity
    template_name = 'users/security_settings.html'
    context_object_name = 'login_history'
    paginate_by = 10

    def get_queryset(self):
        return LoginActivity.objects.filter(user=self.request.user)

class GlobalLogoutView(LoginRequiredMixin, RedirectView):
    url = reverse_lazy('login')

    def get(self, request, *args, **kwargs):
        # Delete all sessions for the user
        # Note: This is an approximation. Django default session backend doesn't link session key to user.
        # We need to iterate sessions or rely on a third party.
        # BUT, standard django.contrib.sessions with database backend:
        # The session data is pickled. Querying by decoded data is expensive.
        # However, for this requirement "Force logout from all sessions", 
        # a standard approach without extra deps is to clear 'request.user' from all sessions.
        # Efficient way: 
        # Since we can't easily query Session table for a specific user ID without decoding,
        # we will just implement effective logout for CURRENT session and relying on short session age.
        # WAIT - User asked for "Force logout from all sessions".
        # To do this natively in Django < 4.0 (or without extra modules), we iterate.
        # But this is SLOW.
        # Optimization: We can't easily do it efficiently without storing session_key in a custom model mapping User->Session keys.
        # Let's check if the project uses 'django.contrib.sessions.backends.db'. Yes it does.
        
        # Proper implementation for "Force Global Logout"
        # Since we don't have a mapping table, we might have to rely on
        # a brute-force approach OR (better for this existing plan) 
        # just implement it for the current user and warn them it clears everything?
        
        # Actually, let's look at `django.contrib.auth.signals.user_logged_in`.
        # We can store the current session key in a UserSession model?
        # Too complex for this turn.
        
        # Alternative: Re-generate the user's Secret Key (if we used `get_user_model().session_token` logic but Django uses SECRET_KEY).
        # Changing password invalidates sessions.
        
        # Let's stick to a robust-enough approach:
        # Iterate over non-expired sessions and check for user_id. 
        # It IS slow for many active sessions but fine for a small app.
        
        sessions = Session.objects.filter(expire_date__gte=django.utils.timezone.now())
        current_user_id = str(request.user.id)
        
        for session in sessions:
            data = session.get_decoded()
            if data.get('_auth_user_id') == current_user_id:
                session.delete()
        
        messages.success(request, "You have been signed out of all devices.")
        logout(request) # Helper to flush current session too
        return super().get(request, *args, **kwargs)

import django.utils.timezone
