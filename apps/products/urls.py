from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryTreeView

router = DefaultRouter()
router.register('', ProductViewSet, basename='product')

urlpatterns = [
    path('categories/tree/', CategoryTreeView.as_view(), name='category-tree'),
    path('', include(router.urls)),
]