# from django.contrib import admin

# from .models import Order, Issuing, OutOfStockNotification

# # Register your models here.

# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['id','user', 'order_code', 'first_name', 'status','date_created','date_receive', 'other', 'month', 'year']

#     # ✅ ค้นหาได้จาก ID, ชื่อผู้ใช้, นามสกุล, อีเมล และหมายเหตุ
#     search_fields = ['id', 'user__first_name', 'user__last_name', 'user__email', 'user__username', 'other']

#     def first_name(self, obj):
#         return obj.user.first_name
#     first_name.short_description = 'ชื่อผู้ใช้'  # ตั้งชื่อคอลัมน์ใน Admin

# class IssuingAdmin(admin.ModelAdmin):
#     list_display = ('order', 'product', 'price', 'quantity', 'datecreated', 'month', 'year')
#     # list_display = ['id','order','product','price','quantity','datecreated']

# class OutOfStockNotificationAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'first_name', 'product', 'date_created', 'acknowledged', 'restocked']

#     def first_name(self, obj):
#         return obj.user.first_name
#     first_name.short_description = 'ชื่อผู้ใช้'  # ตั้งชื่อคอลัมน์ใน Admin

# admin.site.register(Order,OrderAdmin)
# admin.site.register(Issuing,IssuingAdmin)
# admin.site.register(OutOfStockNotification,OutOfStockNotificationAdmin)

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Order, Issuing, OutOfStockNotification

# -----------------------------------------------------------------------------
# 1. Inline Model Admin สำหรับ Issuing (รายการเบิก)
#    - นี่คือส่วนที่จะไปแสดงในหน้า Order
# -----------------------------------------------------------------------------
class IssuingInline(admin.TabularInline):
    """
    กำหนดให้ Model 'Issuing' ไปแสดงเป็นตารางในหน้า 'Order'
    """
    model = Issuing
    
    # แสดงฟิลด์เหล่านี้ในตาราง inline
    fields = ('product', 'receiving', 'quantity', 'price', 'note')
    
    # สำหรับ ForeignKey ที่มีข้อมูลเยอะ, autocomplete ช่วยให้หน้าเว็บโหลดเร็ว
    autocomplete_fields = ['product', 'receiving']
    
    extra = 1  # แสดงช่องว่างสำหรับเพิ่มรายการใหม่ 1 แถวเสมอ
    
    # (เราไม่ต้องกำหนด readonly_fields พวก month, year ที่นี่ 
    # เพราะมันถูกจัดการโดย model save() อยู่แล้ว)

# -----------------------------------------------------------------------------
# 2. Model Admin สำหรับ Order (ออเดอร์หลัก)
# -----------------------------------------------------------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # เพิ่ม IssuingInline เข้ามาในหน้า Order
    inlines = [IssuingInline]

    # ✅ list_display: ฟิลด์ที่จะแสดงในหน้า List
    # - เอา 'other' ออกเพราะมันยาว, เอา 'id' ออกเพราะเราใช้ 'order_code'
    list_display = (
        'id', 
        'order_code', 
        'user_full_name', 
        'status', 
        'pay_item', 
        'confirm',
        'date_created', 
        'date_receive',
        'get_total_sum' # แสดงจำนวนรวม (จาก @property)
    )
    
    # ✅ list_display_links: ทำให้คลิกที่ order_code เพื่อเข้าไปแก้ไขได้
    list_display_links = ('order_code',)

    # ✅ list_filter: เพิ่มตัวกรองด้านข้าง (สำคัญมาก)
    list_filter = ('status', 'pay_item', 'confirm', 'date_created', 'date_receive', 'year', 'month')

    # ✅ search_fields: ฟิลด์ที่ใช้ค้นหา
    # - เพิ่ม 'order_code' และ 'items__product__name' (ค้นหาจากชื่อสินค้าในออเดอร์)
    search_fields = (
        'order_code', 
        'user__first_name', 
        'user__last_name', 
        'user__email', 
        'user__username', 
        'other',
        'items__product__product_name' # ค้นหาจากชื่อสินค้าที่อยู่ในออเดอร์นี้
    )
    
    # ✅ list_editable: ทำให้แก้ไขสถานะจากหน้า List ได้เลย (สะดวกมาก)
    list_editable = ('status', 'pay_item', 'confirm')

    # ✅ readonly_fields: ฟิลด์ที่ห้ามแก้ไขในหน้า Admin (เพราะมันถูกเซ็ตอัตโนมัติ)
    readonly_fields = (
        'order_code', 
        'running_number', 
        'date_created', 
        'date_updated', 
        'month', 
        'year',
        'date_pay', 
        'date_approved', 
        'date_received'
    )
    
    # ✅ autocomplete_fields: ช่วยให้การเลือก User เร็วขึ้น
    autocomplete_fields = ['user']

    # ✅ fieldsets: จัดกลุ่มฟิลด์ในหน้าแก้ไข/สร้าง ให้เป็นระเบียบ
    fieldsets = (
        ('ข้อมูลหลัก (สถานะ)', {
            'fields': ('status', 'pay_item', 'confirm')
        }),
        ('ข้อมูลออเดอร์', {
            'fields': ('user', 'order_code', 'other')
        }),
        ('ข้อมูลผู้รับ/ผู้จ่าย', {
            'fields': ('name_sign', 'name_pay', 'surname_pay')
        }),
        ('วันที่สำคัญ', {
            'fields': ('date_receive', 'date_received', 'date_pay', 'date_approved')
        }),
        ('ข้อมูลอัตโนมัติ (ห้ามแก้ไข)', {
            'classes': ('collapse',), # ซ่อนไว้เป็น default
            'fields': ('running_number', 'date_created', 'date_updated', 'month', 'year'),
        }),
    )

    # ฟังก์ชันสำหรับดึงชื่อ-นามสกุลมาแสดง
    @admin.display(description='ชื่อผู้เบิก')
    def user_full_name(self, obj):
        return obj.user.get_full_name()
    
    # (ฟังก์ชัน first_name เดิมของคุณก็ใช้ได้ครับ แต่ get_full_name จะดีกว่า)

# -----------------------------------------------------------------------------
# 3. Model Admin สำหรับ Issuing (หน้ารวมรายการเบิกทั้งหมด)
#    - ถึงแม้เราจะมี inline แล้ว ก็ควรลงทะเบียนไว้ดูภาพรวม
# -----------------------------------------------------------------------------
@admin.register(Issuing)
class IssuingAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_order_link', 'product', 'quantity', 'price', 'datecreated', 'month', 'year')
    list_filter = ('datecreated', 'month', 'year', 'product')
    search_fields = ('order__order_code', 'product__name')
    autocomplete_fields = ['order', 'product', 'receiving']

    # ฟังก์ชันสำหรับสร้าง Link กลับไปหา Order
    @admin.display(description='ออเดอร์')
    def get_order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_code)

# -----------------------------------------------------------------------------
# 4. Model Admin สำหรับ OutOfStockNotification
# -----------------------------------------------------------------------------
@admin.register(OutOfStockNotification)
class OutOfStockNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_full_name', 'product', 'date_created', 'acknowledged', 'restocked')
    list_filter = ('acknowledged', 'restocked', 'date_created', 'product')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'product__name')
    
    # แก้ไขสถานะจากหน้า List
    list_editable = ('acknowledged', 'restocked')
    
    autocomplete_fields = ['user', 'product']

    @admin.display(description='ชื่อผู้ใช้')
    def user_full_name(self, obj):
        return obj.user.get_full_name()

# -----------------------------------------------------------------------------
# 5. หมายเหตุ: ลบการลงทะเบียนแบบเก่า
# admin.site.register(Order,OrderAdmin) # เราใช้ @admin.register แทนแล้ว
# admin.site.register(Issuing,IssuingAdmin) # เราใช้ @admin.register แทนแล้ว
# admin.site.register(OutOfStockNotification,OutOfStockNotificationAdmin) # เราใช้ @admin.register แทนแล้ว
# -----------------------------------------------------------------------------