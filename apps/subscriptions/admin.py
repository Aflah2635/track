from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active', 'max_accounts', 'max_shared_accounts')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'payment_status', 'is_active', 'start_date', 'end_date')
    list_filter = ('plan', 'status', 'payment_status', 'is_active')
    search_fields = ('user__username', 'user__email')
    list_editable = ('status', 'payment_status', 'is_active')
