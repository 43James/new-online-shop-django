from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import MyUser, Profile, WorkGroup

class MyUserAdmin(admin.ModelAdmin):
    list_display = ['username','email', 'is_general', 'is_executive','is_manager','is_admin','date_created']

    # กำหนดฟิลด์สำหรับการกรองใน sidebar
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'groups']

    # กำหนดฟิลด์ที่ใช้ในการค้นหา
    search_fields = ['username', 'email']
    ordering = ['username']

    # กำหนดฟิลด์ที่จะแก้ไขในหน้าแก้ไข
    # fields = ('username', 'email', 'first_name', 'last_name', 'password', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions', 'is_general', 'is_executive','is_manager','is_admin')
    
    # เพิ่มการจัดกลุ่มฟิลด์ในหน้าแก้ไข
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Roles', {'fields': ('is_general', 'is_executive', 'is_manager', 'is_admin')}),
    )
    
admin.site.register(MyUser,MyUserAdmin)
# admin.site.register(MyUser,UserAdmin)



class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id','user','workgroup','position']

admin.site.register(Profile,ProfileAdmin)


class WorkGroupAdmin(admin.ModelAdmin):
    list_display = ['id','work_group']

admin.site.register(WorkGroup,WorkGroupAdmin)
