from django.contrib import admin

from .models import Order, Issuing

# Register your models here.

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id','user','date_created','date_receive', 'other']

class IssuingAdmin(admin.ModelAdmin):
    list_display = ['id','order','product','price','quantity','datecreated']

admin.site.register(Order,OrderAdmin)
admin.site.register(Issuing,IssuingAdmin)