# from django.contrib import admin

# from .models import AssetItem, AssetCode, StorageLocation, Subcategory, AssetCategory

# Register your models here.

# class AssetItemAdmin(admin.ModelAdmin):
#     list_display = ['id','item_name', 'subcategory', 'asset_code','status_assetloan']

#     # ✅ ค้นหาได้จาก ID, ชื่อผู้ใช้, นามสกุล, อีเมล และหมายเหตุ
#     search_fields = ['id', 'item_name', 'asset_code']

# admin.site.register(AssetItem,AssetItemAdmin)


# class AssetCodeAdmin(admin.ModelAdmin):
#     list_display = ['id','asset_type', 'asset_kind', 'asset_character','serial_year']

#     # ✅ ค้นหาได้จาก ID, ชื่อผู้ใช้, นามสกุล, อีเมล และหมายเหตุ
#     search_fields = ['id', 'asset_type', 'serial_year']

# admin.site.register(AssetCode,AssetCodeAdmin)

from django.contrib import admin
from .models import (
    AssetCategory, Subcategory, StorageLocation,
    AssetCode, AssetItem, OrderAssetLoan, IssuingAssetLoan
)


# ==========================
# หมวดหมู่หลัก และหมวดหมู่ย่อย
# ==========================
class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name_cate")
    search_fields = ("name_cate",)
    inlines = [SubcategoryInline]


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name_sub", "category")
    search_fields = ("name_sub",)
    list_filter = ("category",)


# ==========================
# สถานที่เก็บ
# ==========================
@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


# ==========================
# รหัสครุภัณฑ์
# ==========================
@admin.register(AssetCode)
class AssetCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "asset_type", "asset_kind", "asset_character", "serial_year")
    search_fields = ("asset_type", "asset_kind", "asset_character", "serial_year")
    list_filter = ("asset_type", "asset_kind")


# ==========================
# รายการครุภัณฑ์
# ==========================
@admin.register(AssetItem)
class AssetItemAdmin(admin.ModelAdmin):
    list_display = (
        "id", "item_name", "subcategory", "asset_code", "unit", "purchase_price",
        "fiscal_year", "lifetime", "annual_depreciation",
        "responsible_person", "storage_location",
        "damage_status", "status_borrowing", "status_assetloan",
    )
    search_fields = ("item_name", "brand_model", "responsible_person")
    list_filter = ("subcategory", "storage_location", "damage_status", "status_borrowing")
    readonly_fields = ("annual_depreciation", "date_asset_created", "date_asset_updated", "qr_code")
    fieldsets = (
        ("ข้อมูลครุภัณฑ์", {
            "fields": ("item_name", "subcategory", "asset_code", "brand_model", "unit", "purchase_price")
        }),
        ("การใช้งาน", {
            "fields": ("purchase_date", "fiscal_year", "lifetime", "used_years", "annual_depreciation")
        }),
        ("สถานะ", {
            "fields": ("damage_status", "status_borrowing", "status_assetloan")
        }),
        ("สถานที่และผู้รับผิดชอบ", {
            "fields": ("storage_location", "responsible_person")
        }),
        ("รูปภาพ & QR Code", {
            "fields": ("asset_image", "qr_code", "notes")
        }),
        ("เวลา", {
            "fields": ("date_asset_created", "date_asset_updated")
        }),
    )


# ==========================
# ออเดอร์ยืมครุภัณฑ์
# ==========================
class IssuingAssetLoanInline(admin.TabularInline):
    model = IssuingAssetLoan
    extra = 1


@admin.register(OrderAssetLoan)
class OrderAssetLoanAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "date_created", "date_due", "status_return", "date_of_return", "month", "year")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    list_filter = ("status", "month", "year")
    inlines = [IssuingAssetLoanInline]
    readonly_fields = ("month", "year", "date_created", "date_updated")


# ==========================
# รายการครุภัณฑ์ในออเดอร์
# ==========================
@admin.register(IssuingAssetLoan)
class IssuingAssetLoanAdmin(admin.ModelAdmin):
    list_display = ("id", "order_asset", "asset", "date_created", "month", "year")
    search_fields = ("order_asset__id", "asset__item_name")
    list_filter = ("month", "year")
    readonly_fields = ("month", "year", "date_created")
