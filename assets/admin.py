from django.contrib import admin

from .models import AssetItem, AssetCode, StorageLocation, Subcategory, AssetCategory

# Register your models here.

class AssetItemAdmin(admin.ModelAdmin):
    list_display = ['id','item_name', 'subcategory', 'asset_code','status_assetloan']

    # ✅ ค้นหาได้จาก ID, ชื่อผู้ใช้, นามสกุล, อีเมล และหมายเหตุ
    search_fields = ['id', 'item_name', 'asset_code']

admin.site.register(AssetItem,AssetItemAdmin)


class AssetCodeAdmin(admin.ModelAdmin):
    list_display = ['id','asset_type', 'asset_kind', 'asset_character','serial_year']

    # ✅ ค้นหาได้จาก ID, ชื่อผู้ใช้, นามสกุล, อีเมล และหมายเหตุ
    search_fields = ['id', 'asset_type', 'serial_year']

admin.site.register(AssetCode,AssetCodeAdmin)
