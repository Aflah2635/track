from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, RedirectView, TemplateView, View
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from apps.notifications.utils import send_tracked_email
from .forms import CustomUserCreationForm, ProfileUpdateForm
from .models import LoginActivity

from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me', False)
        if remember_me:
            # 30 days
            self.request.session.set_expiry(2592000)
        else:
            # Browser close
            self.request.session.set_expiry(0)
            
        return super().form_valid(form)

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_form'] = ProfileUpdateForm(instance=self.request.user)
        context['password_form'] = PasswordChangeForm(self.request.user)
        
        # Determine if session is remembered
        # If expiry is 0, it expires on browser close. Otherwise it's remembered.
        expiry_age = self.request.session.get_expiry_age()
        is_remembered = expiry_age > 0 and not self.request.session.get_expire_at_browser_close()
        
        context['session_remembered'] = is_remembered
        context['session_active'] = "Yes" if self.request.user.is_authenticated else "No"
        
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

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        # Send verification email
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verify_url = self.request.build_absolute_uri(
            reverse_lazy('verify_email', kwargs={'uidb64': uid, 'token': token})
        )
        context = {
            'user': user,
            'verify_url': verify_url,
        }
        send_tracked_email(
            email_type='VERIFICATION',
            subject='Verify Your Email Address',
            template_name='verify_email',
            context=context,
            recipient_list=[user.email],
            user=user
        )
        messages.success(self.request, 'Account created! Please check your email to verify your account.')
        return response

class VerifyEmailView(View):
    def get(self, request, uidb64, token):
        User = get_user_model()
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_verified = True
            user.save()
            messages.success(request, 'Your email has been verified. You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'The verification link is invalid or has expired.')
            return redirect('login')

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
