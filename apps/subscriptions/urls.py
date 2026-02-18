from django.urls import path
from .views import PricingView, SubscriptionSwitchView

urlpatterns = [
    path('pricing/', PricingView.as_view(), name='pricing'),
    path('subscribe/<int:pk>/', SubscriptionSwitchView.as_view(), name='subscribe'),
]
