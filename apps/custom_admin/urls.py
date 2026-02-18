from django.urls import path
from .views import (
    AdminDashboardView, 
    UserListView, UserCreateView, UserUpdateView, UserDeleteView, 
    AccountListView, AccountCreateView, AccountUpdateView, AccountDeleteView,
    CategoryListView, CategoryCreateView, CategoryUpdateView, CategoryDeleteView,
    SubscriptionPlanListView, SubscriptionPlanCreateView, SubscriptionPlanUpdateView, SubscriptionPlanDeleteView,
    UserSubscriptionListView, UserSubscriptionCreateView, UserSubscriptionUpdateView, UserSubscriptionDeleteView,
    NotificationListView, BroadcastCreateView, NotificationDeleteView,
    MaintenanceStateUpdateView
)

app_name = 'custom_admin'

urlpatterns = [
    path('', AdminDashboardView.as_view(), name='dashboard'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/update/', UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),

    
    # Accounts
    path('accounts/', AccountListView.as_view(), name='account_list'),
    path('accounts/create/', AccountCreateView.as_view(), name='account_create'),
    path('accounts/<int:pk>/update/', AccountUpdateView.as_view(), name='account_update'),
    path('accounts/<int:pk>/delete/', AccountDeleteView.as_view(), name='account_delete'),

    # Categories
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),

    # Subscriptions
    path('plans/', SubscriptionPlanListView.as_view(), name='plan_list'),
    path('plans/create/', SubscriptionPlanCreateView.as_view(), name='plan_create'),
    path('plans/<int:pk>/update/', SubscriptionPlanUpdateView.as_view(), name='plan_update'),
    path('plans/<int:pk>/delete/', SubscriptionPlanDeleteView.as_view(), name='plan_delete'),

    path('user-subscriptions/', UserSubscriptionListView.as_view(), name='user_subscription_list'),
    path('user-subscriptions/create/', UserSubscriptionCreateView.as_view(), name='user_subscription_create'),
    path('user-subscriptions/<int:pk>/update/', UserSubscriptionUpdateView.as_view(), name='user_subscription_update'),
    path('user-subscriptions/<int:pk>/delete/', UserSubscriptionDeleteView.as_view(), name='user_subscription_delete'),

    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('broadcast/', BroadcastCreateView.as_view(), name='broadcast_create'),
    path('notifications/<int:pk>/delete/', NotificationDeleteView.as_view(), name='notification_delete'),

    # System
    path('system/', MaintenanceStateUpdateView.as_view(), name='system_control'),
]
