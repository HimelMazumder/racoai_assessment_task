from django.core.cache import cache
from .models import Category, Product

def get_category_tree(parent=None):
    categories = Category.objects.filter(parent=parent)
    tree = []

    for category in categories:
        tree.append({
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "subcategories": get_category_tree(category), # DFS recursive function calls
        })
    
    return tree

def get_cached_category_tree():
    cache_key = "full_category_tree"

    tree = cache.get(cache_key)

    if tree is None:
        tree = get_category_tree(parent=None)
        cache.set(cache_key, tree, timeout=43200) # 12 hours

    return tree

# to get related products from the sub tree 

def get_subtree_ids(category):
    ids = [category.id]

    for sub in category.subcategories.all():
        ids.extend(get_subtree_ids(sub)) # Recursive DFS calls to get all subtree ids
    
    return ids

def get_related_products(product_id, limit=10):
    try:
        product = Product.objects.get(id=product_id)

        # for product with no category, or category set as null
        if not product.category:
            return []

        category_ids = get_subtree_ids(product.category)

        related = Product.objects.filter(
            category_id__in=category_ids,
            status='active',
        ).exclude(id=product_id)[:limit]

        return list(related)

    except Product.DoesNotExist:
        return []