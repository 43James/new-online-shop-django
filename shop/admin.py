from django.contrib import admin
from .models import Category, Product, Stock, Subcategory,Suppliers,Receiving, Total_Quantity, MonthlyStockRecord

class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'product_name']
    # prepopulated_fields = {'slug':['product_id']}

class ReceivingAdmin(admin.ModelAdmin):
    @admin.display(description='ชื่อสินค้า')
    def product_name(self, obj):
        return obj.product.product_name

    list_display = ['product', 'product_name']
    # prepopulated_fields = {'quantity':['quantityreceived']}

class MonthlyStockRecordAdmin(admin.ModelAdmin):
    @admin.display(description='IDสินค้า')
    def product_id(self, obj):
        return obj.product.product_id

    @admin.display(description='ชื่อสินค้า')
    def product_name(self, obj):
        return obj.product.product_name

    list_display = ['product_id', 'product_name', 'month', 'year', 'end_of_month_balance', 'total_price']

admin.site.register(MonthlyStockRecord,MonthlyStockRecordAdmin)
admin.site.register(Suppliers)
admin.site.register(Receiving,ReceivingAdmin)
admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Product, ProductAdmin)
admin.site.register(Stock)
admin.site.register(Total_Quantity)





