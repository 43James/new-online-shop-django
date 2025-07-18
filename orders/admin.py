from django.contrib import admin

from .models import Order, Issuing, OutOfStockNotification

# Register your models here.

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id','user', 'first_name', 'status','date_created','date_receive', 'other', 'month', 'year']

    # ✅ ค้นหาได้จาก ID, ชื่อผู้ใช้, นามสกุล, อีเมล และหมายเหตุ
    search_fields = ['id', 'user__first_name', 'user__last_name', 'user__email', 'user__username', 'other']

    def first_name(self, obj):
        return obj.user.first_name
    first_name.short_description = 'ชื่อผู้ใช้'  # ตั้งชื่อคอลัมน์ใน Admin

class IssuingAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'price', 'quantity', 'datecreated', 'month', 'year')
    # list_display = ['id','order','product','price','quantity','datecreated']

class OutOfStockNotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'first_name', 'product', 'date_created', 'acknowledged', 'restocked']

    def first_name(self, obj):
        return obj.user.first_name
    first_name.short_description = 'ชื่อผู้ใช้'  # ตั้งชื่อคอลัมน์ใน Admin

admin.site.register(Order,OrderAdmin)
admin.site.register(Issuing,IssuingAdmin)
admin.site.register(OutOfStockNotification,OutOfStockNotificationAdmin)