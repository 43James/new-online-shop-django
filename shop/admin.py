from django.contrib import admin
from .models import Category, Product, Stock, Subcategory,Suppliers,Receiving, Total_Quantity, TotalQuantity, MonthlyStockRecord

class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'product_name']
    # prepopulated_fields = {'slug':['product_id']}

class ReceivingAdmin(admin.ModelAdmin):
    list_display = ['product']
    # prepopulated_fields = {'quantity':['quantityreceived']}



admin.site.register(MonthlyStockRecord)
admin.site.register(Suppliers)
admin.site.register(Receiving,ReceivingAdmin)
admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Product, ProductAdmin)
admin.site.register(Stock)
admin.site.register(Total_Quantity)
admin.site.register(TotalQuantity)




