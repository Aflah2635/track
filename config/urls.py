"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.core.views import home, dashboard
from apps.users.views import SignUpView
from apps.accounts.views import (
    AccountCreateView, share_account, revoke_access,
    AccountListView, AccountUpdateView, AccountDeleteView
)
from apps.transactions.views import (
    TransactionCreateView, 
    TransactionUpdateView, TransactionDeleteView
)
from apps.transactions.statement_views import StatementPDFView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('audit/', include('apps.users.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup/', SignUpView.as_view(), name='signup'),
    
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    
    path('accounts/manage/', AccountListView.as_view(), name='manage_accounts'),
    path('accounts/create/', AccountCreateView.as_view(), name='create_account'),
    path('accounts/<int:pk>/share/', share_account, name='share_account'),
    path('accounts/<int:pk>/revoke/<int:user_id>/', revoke_access, name='revoke_access'),
    path('accounts/<int:pk>/update/', AccountUpdateView.as_view(), name='update_account'),
    path('accounts/<int:pk>/delete/', AccountDeleteView.as_view(), name='delete_account'),
    
    path('setup/account/', AccountCreateView.as_view(), name='add_account'),
    path('transaction/new/', TransactionCreateView.as_view(), name='add_transaction'),
    path('transaction/<int:pk>/edit/', TransactionUpdateView.as_view(), name='edit_transaction'),
    path('transaction/<int:pk>/delete/', TransactionDeleteView.as_view(), name='delete_transaction'),
    path('statement/<int:account_id>/', StatementPDFView.as_view(), name='statement_pdf'),
    path('notifications/', include('apps.notifications.urls')),
    path('categories/', include('apps.categories.urls')),
]
