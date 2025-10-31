# from django.contrib import admin
# from .models import Category, Product, Stock, Subcategory,Suppliers,Receiving, Total_Quantity, MonthlyStockRecord

# class ProductAdmin(admin.ModelAdmin):
#     list_display = ['product_id', 'product_name']
#     # prepopulated_fields = {'slug':['product_id']}

# # class ReceivingAdmin(admin.ModelAdmin):
# #     @admin.display(description='ชื่อสินค้า')
# #     def product_name(self, obj):
# #         return obj.product.product_name

# #     list_display = ['product', 'product_name']
#     # prepopulated_fields = {'quantity':['quantityreceived']}

# class ReceivingAdmin(admin.ModelAdmin):
#     @admin.display(description='ชื่อสินค้า')
#     def product_name(self, obj):
#         return obj.product.product_name

#     # แสดงทุกฟิลด์ที่สามารถแก้ไขได้ในหน้าแก้ไข (Edit Form)
#     fields = [field.name for field in Receiving._meta.fields if field.editable and field.name not in ['id', 'date_created', 'date_updated']]
    
#     search_fields = ['product__product_id', 'product__product_name', 'month', 'year',]

#     # (Optional) แสดงฟิลด์ทั้งหมดใน list view ด้วย
#     list_display = [field.name for field in Receiving._meta.fields]

# class MonthlyStockRecordAdmin(admin.ModelAdmin):
#     @admin.display(description='IDสินค้า')
#     def product_id(self, obj):
#         return obj.product.product_id

#     @admin.display(description='ชื่อสินค้า')
#     def product_name(self, obj):
#         return obj.product.product_name
    
#     search_fields = ['product__product_id', 'product__product_name', 'month', 'year',]

#     list_display = ['product_id', 'product_name', 'month', 'year', 'end_of_month_balance', 'total_price']

# admin.site.register(MonthlyStockRecord,MonthlyStockRecordAdmin)
# admin.site.register(Suppliers)
# admin.site.register(Receiving,ReceivingAdmin)
# admin.site.register(Category)
# admin.site.register(Subcategory)
# admin.site.register(Product, ProductAdmin)
# admin.site.register(Stock)
# admin.site.register(Total_Quantity)



# shop/admin.py

from django.contrib import admin
from django.utils.html import format_html # Import เพิ่ม
from .models import (
    Category, Subcategory, Product, 
    Suppliers, Receiving, MonthlyStockRecord, 
    Stock, Total_Quantity
)

# ----------------------------------------------------
# 1. ใช้ Inline Admin สำหรับ Subcategory
# ----------------------------------------------------
class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1 # แสดงแถวว่าง 1 แถวสำหรับเพิ่มใหม่

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name_cate',)
    search_fields = ('name_cate',)
    inlines = [SubcategoryInline] # นำ Subcategory มาไว้ข้างใน

# ----------------------------------------------------
# 2. Product Admin (แก้ไข)
# ----------------------------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('img_preview', 'product_id', 'product_name', 'category', 'quantityinstock', 'unit')
    list_filter = ('category', 'category__category') # กรองตามหมวดหมู่ย่อยและหลัก
    
    # vvvv นี่คือส่วนสำคัญที่แก้ Error E040 vvvv
    search_fields = ('product_name', 'product_id') 
    
    autocomplete_fields = ('category',) # ทำให้ช่องเลือก category ค้นหาได้
    
    # ฟังก์ชันแสดงรูปภาพ (ปรับจาก .img() ใน model)
    @admin.display(description='รูปภาพ')
    def img_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="50px" />', obj.image.url)
        return 'ไม่มีรูป'

# ----------------------------------------------------
# 3. Suppliers Admin
# ----------------------------------------------------
@admin.register(Suppliers)
class SuppliersAdmin(admin.ModelAdmin):
    list_display = ('supname', 'contactname', 'phone')
    
    # vvvv เพิ่ม search_fields (สำคัญสำหรับ ReceivingAdmin) vvvv
    search_fields = ('supname', 'contactname', 'phone', 'taxnumber')

# ----------------------------------------------------
# 4. Receiving Admin (แก้ไข)
# ----------------------------------------------------
@admin.register(Receiving)
class ReceivingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'product', 
        'suppliers', 
        'quantityreceived', 
        'quantity', 
        'unitprice', 
        'date_received',
        'month',
        'year'
    )
    list_filter = ('date_received', 'month', 'year', 'suppliers', 'product')
    
    # vvvv search_fields ที่คุณเพิ่มมานั้นถูกต้องแล้ว vvvv
    search_fields = ['product__product_id', 'product__product_name', 'suppliers__supname']

    # vvvv เพิ่ม autocomplete_fields เพื่อให้หน้า Admin โหลดเร็ว vvvv
    autocomplete_fields = ['product', 'suppliers']
    
    # (โค้ด 'fields = ...' และ 'list_display = ...' ที่สร้างอัตโนมัติ 
    #  ไม่จำเป็นแล้ว การระบุชัดเจนแบบนี้ดีกว่าครับ)

# ----------------------------------------------------
# 5. ลงทะเบียน Model ที่เหลือ
# ----------------------------------------------------
@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    # ทำให้ค้นหา Subcategory ได้ (จำเป็นสำหรับ ProductAdmin)
    list_display = ('name_sub', 'category')
    search_fields = ('name_sub', 'category__name_cate')

@admin.register(MonthlyStockRecord)
class MonthlyStockRecordAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'product_name', 'month', 'year', 'end_of_month_balance', 'total_price']
    search_fields = ['product__product_id', 'product__product_name', 'month', 'year']
    list_filter = ('year', 'month')
    autocomplete_fields = ['product'] # เพิ่ม

    @admin.display(description='ID สินค้า')
    def product_id(self, obj):
        return obj.product.product_id

    @admin.display(description='ชื่อสินค้า')
    def product_name(self, obj):
        return obj.product.product_name

# (Model 2 ตัวนี้ผมไม่แน่ใจว่าคุณใช้ทำอะไร แต่ผมลงทะเบียนไว้ให้ก่อน)
admin.site.register(Stock)
admin.site.register(Total_Quantity)

