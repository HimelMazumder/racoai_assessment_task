from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product, Category
from .serializers import ProductSerializer
from .services import get_cached_category_tree, get_related_products

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(status='active').select_related('category')
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    @action(detail=True, methods=['get'], url_path='related')
    def related(self, request, pk=None):
        products = get_related_products(pk)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

class CategoryTreeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        tree = get_cached_category_tree()
        return Response(tree)