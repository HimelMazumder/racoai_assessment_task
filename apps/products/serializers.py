from rest_framework import serializers
from .models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False
    )

    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'description', 'price', 'stock', 'status', 'category', 'category_id', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']