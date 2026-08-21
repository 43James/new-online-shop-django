import django_filters
from .models import Product, Subcategory

class FilterProduct(django_filters.FilterSet):
    class Meta:
        model = Product
        fields = ['id','category']
        
class FilterSubcategory(django_filters.FilterSet):
    class Meta:
        model = Subcategory
        fields = ['id','name_sub','category']

