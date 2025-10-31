# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin

# from .models import MyUser, Profile, WorkGroup

# class MyUserAdmin(admin.ModelAdmin):
#     list_display = ['username','email', 'is_general', 'is_executive', 'is_manager', 'is_warehouse_manager', 'is_admin','date_created']

#     # กำหนดฟิลด์สำหรับการกรองใน sidebar
#     list_filter = ['is_staff', 'is_superuser', 'is_active', 'groups']

#     # กำหนดฟิลด์ที่ใช้ในการค้นหา
#     search_fields = ['username', 'email']
#     ordering = ['username']

#     # กำหนดฟิลด์ที่จะแก้ไขในหน้าแก้ไข
#     # fields = ('username', 'email', 'first_name', 'last_name', 'password', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions', 'is_general', 'is_executive','is_manager','is_admin')
    
#     # เพิ่มการจัดกลุ่มฟิลด์ในหน้าแก้ไข
#     fieldsets = (
#         (None, {'fields': ('username', 'password')}),
#         ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
#         ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#         ('Important dates', {'fields': ('last_login', 'date_joined')}),
#         ('Roles', {'fields': ('is_general', 'is_executive', 'is_manager', 'is_warehouse_manager', 'is_admin')}),
#     )
    
# admin.site.register(MyUser,MyUserAdmin)
# # admin.site.register(MyUser,UserAdmin)



# class ProfileAdmin(admin.ModelAdmin):
#     list_display = ['id','user','workgroup','position']

# admin.site.register(Profile,ProfileAdmin)


# class WorkGroupAdmin(admin.ModelAdmin):
#     list_display = ['id','work_group']

# admin.site.register(WorkGroup,WorkGroupAdmin)

# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin # Import UserAdmin
from .models import MyUser, Profile, WorkGroup

# ----------------------------------------------------
# 1. สร้าง Profile Inline
# ----------------------------------------------------
class ProfileInline(admin.StackedInline): # ใช้ StackedInline จะดูง่ายกว่า
    model = Profile
    can_delete = False
    verbose_name_plural = 'ข้อมูลโปรไฟล์'
    fk_name = 'user'
    autocomplete_fields = ['workgroup'] # ทำให้ช่อง 'กลุ่มงาน' ค้นหาได้

# ----------------------------------------------------
# 2. MyUser Admin (แก้ไข)
# ----------------------------------------------------
@admin.register(MyUser)
class MyUserAdmin(UserAdmin): # <-- เปลี่ยนเป็น UserAdmin
    inlines = (ProfileInline, ) # <-- นำ Profile มาใส่
    
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name', 
        'is_staff', 
        'is_general', # เพิ่มฟิลด์ Role ของคุณ
        'is_manager', 
        'is_warehouse_manager'
    )
    
    list_filter = UserAdmin.list_filter + ('is_general', 'is_manager', 'is_warehouse_manager')
    
    # vvvv search_fields ของคุณถูกต้องแล้ว vvvv
    search_fields = ('username', 'email', 'first_name', 'last_name')

    # vvvv นำ fieldsets เดิมของ UserAdmin มา + เพิ่ม 'Roles' ของคุณเข้าไป vvvv
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('perfix', 'first_name', 'last_name', 'email')}),
        
        # เพิ่มกลุ่ม 'Custom Roles' ที่คุณสร้างไว้
        ('Roles', {'fields': (
            'is_general', 
            'is_manager', 
            'is_warehouse_manager', 
            'is_executive', 
            'is_admin'
        )}),
        
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # ทำให้สามารถแก้ไข Profile inline ในหน้าสร้าง User ใหม่ได้
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(MyUserAdmin, self).get_inline_instances(request, obj)

# ----------------------------------------------------
# 3. WorkGroup Admin
# ----------------------------------------------------
@admin.register(WorkGroup)
class WorkGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'work_group']
    search_fields = ['work_group'] # <-- เพิ่ม search_fields

# ----------------------------------------------------
# 4. ลบการลงทะเบียนเก่า (เพราะใช้ @admin.register แล้ว)
# ----------------------------------------------------
# admin.site.register(MyUser,MyUserAdmin) # ไม่ต้องใช้
# admin.site.register(Profile,ProfileAdmin) # ไม่ต้องใช้ (ไปรวมกับ User แล้ว)
# admin.site.register(WorkGroup,WorkGroupAdmin) # ไม่ต้องใช้