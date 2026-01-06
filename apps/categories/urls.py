from django.urls import path
from .views import CategoryListView, CategoryCreateView, CategoryUpdateView, CategoryDeleteView

urlpatterns = [
    path('', CategoryListView.as_view(), name='category_list'),
    path('add/', CategoryCreateView.as_view(), name='category_add'),
    path('<int:pk>/edit/', CategoryUpdateView.as_view(), name='category_edit'),
    path('<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),
]
