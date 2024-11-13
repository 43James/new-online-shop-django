from django.contrib import admin

from .models import Order, Issuing, Approvereport

# Register your models here.

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id','user','status','date_created','date_receive', 'other', 'month', 'year']

class IssuingAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'receiving', 'price', 'quantity', 'datecreated', 'month', 'year')
    # list_display = ['id','order','product','price','quantity','datecreated']

class ApprovereportAdmin(admin.ModelAdmin):
    list_display = ['id','approve','name_sign1','name_sign2','name_approve', 'month', 'year']

admin.site.register(Order,OrderAdmin)
admin.site.register(Issuing,IssuingAdmin)
admin.site.register(Approvereport,ApprovereportAdmin)