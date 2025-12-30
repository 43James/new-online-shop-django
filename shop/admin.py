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

# from django.contrib import admin
# from django.utils.html import format_html # Import เพิ่ม
# from .models import (
#     Category, Subcategory, Product, 
#     Suppliers, Receiving, MonthlyStockRecord, 
#     Stock, Total_Quantity
# )

# # ----------------------------------------------------
# # 1. ใช้ Inline Admin สำหรับ Subcategory
# # ----------------------------------------------------
# class SubcategoryInline(admin.TabularInline):
#     model = Subcategory
#     extra = 1 # แสดงแถวว่าง 1 แถวสำหรับเพิ่มใหม่

# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('name_cate',)
#     search_fields = ('name_cate',)
#     inlines = [SubcategoryInline] # นำ Subcategory มาไว้ข้างใน

# # ----------------------------------------------------
# # 2. Product Admin (แก้ไข)
# # ----------------------------------------------------
# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('img_preview', 'product_id', 'product_name', 'category', 'quantityinstock', 'unit')
#     list_filter = ('category', 'category__category') # กรองตามหมวดหมู่ย่อยและหลัก
    
#     # vvvv นี่คือส่วนสำคัญที่แก้ Error E040 vvvv
#     search_fields = ('product_name', 'product_id') 
    
#     autocomplete_fields = ('category',) # ทำให้ช่องเลือก category ค้นหาได้
    
#     # ฟังก์ชันแสดงรูปภาพ (ปรับจาก .img() ใน model)
#     @admin.display(description='รูปภาพ')
#     def img_preview(self, obj):
#         if obj.image:
#             return format_html('<img src="{}" height="50px" />', obj.image.url)
#         return 'ไม่มีรูป'

# # ----------------------------------------------------
# # 3. Suppliers Admin
# # ----------------------------------------------------
# @admin.register(Suppliers)
# class SuppliersAdmin(admin.ModelAdmin):
#     list_display = ('supname', 'contactname', 'phone')
    
#     # vvvv เพิ่ม search_fields (สำคัญสำหรับ ReceivingAdmin) vvvv
#     search_fields = ('supname', 'contactname', 'phone', 'taxnumber')

# # ----------------------------------------------------
# # 4. Receiving Admin (แก้ไข)
# # ----------------------------------------------------
# @admin.register(Receiving)
# class ReceivingAdmin(admin.ModelAdmin):
#     list_display = (
#         'id', 
#         'product', 
#         'suppliers', 
#         'quantityreceived', 
#         'quantity', 
#         'unitprice', 
#         'date_received',
#         'month',
#         'year'
#     )
#     list_filter = ('date_received', 'month', 'year', 'suppliers', 'product')
    
#     # vvvv search_fields ที่คุณเพิ่มมานั้นถูกต้องแล้ว vvvv
#     search_fields = ['product__product_id', 'product__product_name', 'suppliers__supname']

#     # vvvv เพิ่ม autocomplete_fields เพื่อให้หน้า Admin โหลดเร็ว vvvv
#     autocomplete_fields = ['product', 'suppliers']
    
#     # (โค้ด 'fields = ...' และ 'list_display = ...' ที่สร้างอัตโนมัติ 
#     #  ไม่จำเป็นแล้ว การระบุชัดเจนแบบนี้ดีกว่าครับ)

# # ----------------------------------------------------
# # 5. ลงทะเบียน Model ที่เหลือ
# # ----------------------------------------------------
# @admin.register(Subcategory)
# class SubcategoryAdmin(admin.ModelAdmin):
#     # ทำให้ค้นหา Subcategory ได้ (จำเป็นสำหรับ ProductAdmin)
#     list_display = ('name_sub', 'category')
#     search_fields = ('name_sub', 'category__name_cate')

# @admin.register(MonthlyStockRecord)
# class MonthlyStockRecordAdmin(admin.ModelAdmin):
#     list_display = ['product_id', 'product_name', 'month', 'year', 'end_of_month_balance', 'total_price']
#     search_fields = ['product__product_id', 'product__product_name', 'month', 'year']
#     list_filter = ('year', 'month')
#     autocomplete_fields = ['product'] # เพิ่ม

#     @admin.display(description='ID สินค้า')
#     def product_id(self, obj):
#         return obj.product.product_id

#     @admin.display(description='ชื่อสินค้า')
#     def product_name(self, obj):
#         return obj.product.product_name

# # (Model 2 ตัวนี้ผมไม่แน่ใจว่าคุณใช้ทำอะไร แต่ผมลงทะเบียนไว้ให้ก่อน)
# admin.site.register(Stock)
# admin.site.register(Total_Quantity)



# import re  # <--- เพิ่ม: สำหรับแยกตัวเลขออกจากตัวอักษร
# from django.contrib import admin
# from django.db import transaction  # <--- เพิ่ม: สำหรับจัดการ Database Transaction
# from django.contrib import messages  # <--- เพิ่ม: สำหรับแจ้งเตือนข้อความ
# from reversion.admin import VersionAdmin
# from django.utils.html import format_html
# from .models import (
#     Category, Subcategory, Product, 
#     Suppliers, Receiving, MonthlyStockRecord, 
#     Stock, Total_Quantity
# )

# # ====================================================
# # ส่วนฟังก์ชันช่วยสำหรับปุ่ม "ปรับเลื่อนลำดับรหัส" (เพิ่มใหม่)
# # ====================================================

# def natural_sort_key(s):
#     """ฟังก์ชันช่วยเรียงลำดับแบบธรรมชาติ เช่น สนง.2 จะมาก่อน สนง.10"""
#     # ดึงค่า product_id ออกมาจาก object ก่อนส่งเข้า regex
#     return [int(text) if text.isdigit() else text.lower()
#             for text in re.split('([0-9]+)', s.product_id)]

# @admin.action(description='🔄 ปรับรหัสพัสดุให้เรียงต่อกัน (Re-sequence IDs)')
# def reorder_product_ids(modeladmin, request, queryset):
#     # 1. ดึงข้อมูลและเรียงลำดับให้ถูกต้องก่อน
#     products = list(queryset)
#     products.sort(key=natural_sort_key)

#     if not products:
#         return

#     try:
#         with transaction.atomic():
#             # ดึง Prefix และ เลขเริ่มต้น จากตัวแรกสุดที่เลือก
#             first_id = products[0].product_id
#             match = re.match(r"^(\D+)(\d+)$", first_id)
            
#             if not match:
#                 messages.error(request, f"รหัสพัสดุ '{first_id}' รูปแบบไม่ถูกต้อง (ต้องเป็น ตัวอักษร+ตัวเลข)")
#                 return

#             prefix = match.group(1)
#             start_number = int(match.group(2))
            
#             # ขั้นตอนที่ 1: เปลี่ยนเป็นชื่อชั่วคราว (กัน Error เรื่องชื่อซ้ำ)
#             temp_map = []
#             for product in products:
#                 original_id = product.product_id
#                 product.product_id = f"TEMP_{original_id}"
#                 product.save()
#                 temp_map.append(product)

#             # ขั้นตอนที่ 2: เปลี่ยนเป็นเลขใหม่ที่เรียงกัน
#             current_number = start_number
#             count = 0
            
#             for product in temp_map:
#                 new_id = f"{prefix}{current_number}"
#                 product.product_id = new_id
#                 product.save()
                
#                 current_number += 1
#                 count += 1

#             messages.success(request, f"จัดเรียงรหัสใหม่สำเร็จ {count} รายการ (เริ่มที่ {prefix}{start_number})")

#     except Exception as e:
#         messages.error(request, f"เกิดข้อผิดพลาด: {str(e)}")


# # ====================================================
# # จบส่วนฟังก์ชันช่วย
# # ====================================================


# # ----------------------------------------------------
# # 1. Inline Admin สำหรับ Subcategory
# # ----------------------------------------------------
# class SubcategoryInline(admin.TabularInline):
#     model = Subcategory
#     extra = 1

# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('name_cate',)
#     search_fields = ('name_cate',)
#     inlines = [SubcategoryInline]

# # ----------------------------------------------------
# # 2. Product Admin (แก้ไขเพิ่ม actions)
# # ----------------------------------------------------
# @admin.register(Product)
# class ProductAdmin(VersionAdmin):
#     list_display = ('img_preview', 'product_id', 'product_name', 'category', 'quantityinstock', 'unit')
#     list_filter = ('category', 'category__category')
#     search_fields = ('product_name', 'product_id')
#     autocomplete_fields = ('category',)
    
#     # <--- เพิ่มบรรทัดนี้: เพื่อเปิดใช้งานปุ่มกดในหน้า Admin
#     actions = [reorder_product_ids] 

#     @admin.display(description='รูปภาพ')
#     def img_preview(self, obj):
#         if obj.image:
#             return format_html('<img src="{}" height="50px" />', obj.image.url)
#         return 'ไม่มีรูป'

# # ----------------------------------------------------
# # 3. Suppliers Admin
# # ----------------------------------------------------
# @admin.register(Suppliers)
# class SuppliersAdmin(admin.ModelAdmin):
#     list_display = ('supname', 'contactname', 'phone')
#     search_fields = ('supname', 'contactname', 'phone', 'taxnumber')

# # ----------------------------------------------------
# # 4. Receiving Admin
# # ----------------------------------------------------
# @admin.register(Receiving)
# class ReceivingAdmin(admin.ModelAdmin):
#     list_display = (
#         'id', 'product', 'suppliers', 'quantityreceived', 
#         'quantity', 'unitprice', 'date_received', 'month', 'year'
#     )
#     list_filter = ('date_received', 'month', 'year', 'suppliers', 'product')
#     search_fields = ['product__product_id', 'product__product_name', 'suppliers__supname']
#     autocomplete_fields = ['product', 'suppliers']

# # ----------------------------------------------------
# # 5. ลงทะเบียน Model ที่เหลือ
# # ----------------------------------------------------
# @admin.register(Subcategory)
# class SubcategoryAdmin(admin.ModelAdmin):
#     list_display = ('name_sub', 'category')
#     search_fields = ('name_sub', 'category__name_cate')

# @admin.register(MonthlyStockRecord)
# class MonthlyStockRecordAdmin(admin.ModelAdmin):
#     list_display = ['product_id', 'product_name', 'month', 'year', 'end_of_month_balance', 'total_price']
#     search_fields = ['product__product_id', 'product__product_name', 'month', 'year']
#     list_filter = ('year', 'month')
#     autocomplete_fields = ['product']

#     @admin.display(description='ID สินค้า')
#     def product_id(self, obj):
#         return obj.product.product_id

#     @admin.display(description='ชื่อสินค้า')
#     def product_name(self, obj):
#         return obj.product.product_name

# admin.site.register(Stock)
# admin.site.register(Total_Quantity)



import re
from django.contrib import admin
from django.db import transaction
from django.contrib import messages
from django.utils.html import format_html
from django.db.models.functions import Length  # <--- จุดที่ 1: เพิ่มบรรทัดนี้ เพื่อใช้ฟังก์ชันนับความยาวตัวอักษร

# ถ้าติดตั้ง django-reversion แล้วให้ใช้บรรทัดนี้
from reversion.admin import VersionAdmin 
# ถ้ายังไม่ได้ติดตั้ง หรือ Error ให้เปลี่ยนเป็น: from django.contrib.admin import ModelAdmin as VersionAdmin

from .models import (
    Category, Subcategory, Product, 
    Suppliers, Receiving, MonthlyStockRecord, 
    Stock, Total_Quantity
)

# ====================================================
# ส่วนฟังก์ชันช่วยสำหรับปุ่ม "ปรับเลื่อนลำดับรหัส"
# ====================================================

def natural_sort_key(s):
    """ฟังก์ชันช่วยเรียงลำดับแบบธรรมชาติ เช่น สนง.2 จะมาก่อน สนง.10"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s.product_id)]

@admin.action(description='🔄 ปรับรหัสพัสดุให้เรียงต่อกัน (Re-sequence IDs)')
def reorder_product_ids(modeladmin, request, queryset):
    # 1. ดึงข้อมูลและเรียงลำดับให้ถูกต้องก่อน
    products = list(queryset)
    products.sort(key=natural_sort_key)

    if not products:
        return

    try:
        with transaction.atomic():
            first_id = products[0].product_id
            match = re.match(r"^(\D+)(\d+)$", first_id)
            
            if not match:
                messages.error(request, f"รหัสพัสดุ '{first_id}' รูปแบบไม่ถูกต้อง (ต้องเป็น ตัวอักษร+ตัวเลข)")
                return

            prefix = match.group(1)
            start_number = int(match.group(2))
            
            # ขั้นตอนที่ 1: เปลี่ยนเป็นชื่อชั่วคราว
            temp_map = []
            for product in products:
                original_id = product.product_id
                product.product_id = f"TEMP_{original_id}"
                product.save()
                temp_map.append(product)

            # ขั้นตอนที่ 2: เปลี่ยนเป็นเลขใหม่ที่เรียงกัน
            current_number = start_number
            count = 0
            
            for product in temp_map:
                new_id = f"{prefix}{current_number}"
                product.product_id = new_id
                product.save()
                
                current_number += 1
                count += 1

            messages.success(request, f"จัดเรียงรหัสใหม่สำเร็จ {count} รายการ (เริ่มที่ {prefix}{start_number})")

    except Exception as e:
        messages.error(request, f"เกิดข้อผิดพลาด: {str(e)}")


# ----------------------------------------------------
# 1. Inline Admin สำหรับ Subcategory
# ----------------------------------------------------
class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name_cate',)
    search_fields = ('name_cate',)
    inlines = [SubcategoryInline]

# ----------------------------------------------------
# 2. Product Admin (แก้ไข)
# ----------------------------------------------------
@admin.register(Product)
class ProductAdmin(VersionAdmin):
    list_display = ('img_preview', 'product_id', 'product_name', 'category', 'quantityinstock', 'unit')
    list_filter = ('category', 'category__category')
    search_fields = ('product_name', 'product_id')
    autocomplete_fields = ('category',)
    
    actions = [reorder_product_ids] 

    # --- จุดที่ 2: เพิ่มฟังก์ชันนี้เพื่อให้หน้า Admin เรียง ค.1, ค.2, ... ค.10 ได้ถูกต้อง ---
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # เรียงตามความยาวของรหัสก่อน แล้วค่อยเรียงตามตัวอักษร
        return qs.annotate(id_len=Length('product_id')).order_by('id_len', 'product_id')
    # ---------------------------------------------------------------------------

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
    search_fields = ('supname', 'contactname', 'phone', 'taxnumber')

# ----------------------------------------------------
# 4. Receiving Admin
# ----------------------------------------------------
@admin.register(Receiving)
class ReceivingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'product', 'suppliers', 'quantityreceived', 
        'quantity', 'unitprice', 'date_received', 'month', 'year'
    )
    list_filter = ('date_received', 'month', 'year', 'suppliers', 'product')
    search_fields = ['product__product_id', 'product__product_name', 'suppliers__supname']
    autocomplete_fields = ['product', 'suppliers']

# ----------------------------------------------------
# 5. ลงทะเบียน Model ที่เหลือ
# ----------------------------------------------------
@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name_sub', 'category')
    search_fields = ('name_sub', 'category__name_cate')

@admin.register(MonthlyStockRecord)
class MonthlyStockRecordAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'product_name', 'month', 'year', 'end_of_month_balance', 'total_price']
    search_fields = ['product__product_id', 'product__product_name', 'month', 'year']
    list_filter = ('year', 'month')
    autocomplete_fields = ['product']

    @admin.display(description='ID สินค้า')
    def product_id(self, obj):
        return obj.product.product_id

    @admin.display(description='ชื่อสินค้า')
    def product_name(self, obj):
        return obj.product.product_name

admin.site.register(Stock)
admin.site.register(Total_Quantity)