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
    AssetCategory, AssetOwnership, AssetReservation, AssetTransferItem, AssetTransferRequest, Subcategory, StorageLocation,
    AssetCode, AssetItem, OrderAssetLoan, IssuingAssetLoan, AssetItemLoan
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
    # 🚨 list_display ถูกแก้ไขเรื่องไวยากรณ์แล้ว
    list_display = (
        "id",
        "order_code",
        "running_number",
        "user", 
        "user_first_name",  # 🚨 ตอนนี้ Django จะมองหา Method ชื่อนี้
        "status", 
        "date_created", 
        "date_of_use", 
        "date_due", 
        "status_return", 
        "date_of_return", 
        "month", 
        "year"
    )
    search_fields = ("order_code","user__username", "user__first_name", "user__last_name")
    list_filter = ("status", "month", "year")
    inlines = [IssuingAssetLoanInline] # สมมติว่า IssuingAssetLoanInline ถูกกำหนดไว้
    readonly_fields = ("month", "year", "date_created", "date_updated")

    # ----------------------------------------------------
    # ✅ เพิ่ม Method 'user_first_name' เข้าไปในคลาส Admin
    # ----------------------------------------------------
    def user_first_name(self, obj):
        """ส่งกลับชื่อต้นของผู้ยืม"""
        # obj คือ OrderAssetLoan instance
        return obj.user.first_name if obj.user and obj.user.first_name else "-"
        
    user_first_name.short_description = "ชื่อผู้ยืม"
    # อนุญาตให้จัดเรียงตามชื่อต้นของผู้ยืมในโมเดล User
    user_first_name.admin_order_field = 'user__first_name' 


# ==========================
# รายการครุภัณฑ์ในออเดอร์
# ==========================
@admin.register(IssuingAssetLoan)
class IssuingAssetLoanAdmin(admin.ModelAdmin):
    list_display = ("id", "order_asset", "asset", "date_created", "month", "year")
    search_fields = ("order_asset__id", "asset__item_name")
    list_filter = ("month", "year")
    readonly_fields = ("month", "year", "date_created")
    

@admin.register(AssetReservation)
class AssetReservationAdmin(admin.ModelAdmin):
    list_display = (
        'asset',
        'user',
        'reserved_date',
        'returning_date',
        'timestamp'
    )
    list_filter = (
        'reserved_date',
        'returning_date',
        'user',
    )
    search_fields = (
        'asset__item_name',
        'user__username',
        'user__first_name',
        'user__last_name',
    )
    raw_id_fields = ('asset', 'user',)

@admin.register(AssetItemLoan)
class AssetItemLoanAdmin(admin.ModelAdmin):
    list_display = (
        'item_name',
        'subcategory',
        'asset_code',
        'storage_location',
        'damage_status',
        'status_assetloan',
        'status_borrowing',
    )
    list_filter = (
        'subcategory',
        'storage_location',
        'damage_status',
        'status_assetloan',
        'status_borrowing',
    )
    search_fields = (
        'item_name',
        'asset_code',
        'brand_model',
        'notes',
    )
    list_editable = (
        'status_assetloan',
        'status_borrowing',
    )
    readonly_fields = (
        'current_loan',
    )

    # ==========================================
# 3. ข้อมูลการครอบครองครุภัณฑ์
# ==========================================
@admin.register(AssetOwnership)
class AssetOwnershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'asset', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'asset__item_name', 'asset__asset_code__serial_year')
    autocomplete_fields = ('user', 'asset') # ช่วยให้เลือกข้อมูลได้ง่ายขึ้นเมื่อมีข้อมูลเยอะ (ต้องตั้ง search_fields ในโมเดลปลายทางด้วย)

# ==========================================
# 4. ระบบใบคำร้องขอเคลื่อนย้าย/ส่งคืน
# ==========================================

# สร้าง Inline เพื่อให้เห็นรายการครุภัณฑ์ย่อยๆ ในหน้าใบคำร้องเดียวกัน
class AssetTransferItemInline(admin.TabularInline):
    model = AssetTransferItem
    extra = 0 # ไม่ให้โชว์บรรทัดว่างๆ ล่วงหน้า
    fields = ('asset', 'action_type', 'condition', 'transfer_from_location', 'transfer_to_location', 'remark')

@admin.register(AssetTransferRequest)
class AssetTransferRequestAdmin(admin.ModelAdmin):
    # นำ request_code มาแสดงแทน id เพื่อให้ดูง่ายและเป็นระบบ
    list_display = ('request_code', 'requester', 'department_name', 'request_date', 'status')
    
    # เพิ่ม year ในการกรองข้อมูล เผื่อต้องการดูคำร้องของแต่ละปี
    list_filter = ('status', 'year', 'request_date', 'head_approved', 'director_approved')
    
    # เพิ่ม request_code เพื่อให้สามารถพิมพ์ค้นหาจากรหัสคำร้องได้โดยตรง
    search_fields = ('request_code', 'requester__first_name', 'requester__last_name', 'id')
    
    # กำหนดให้ฟิลด์เหล่านี้เป็นแบบอ่านอย่างเดียว ป้องกันการแก้ไขด้วยมือ
    readonly_fields = ('request_code', 'running_number', 'year', 'request_date')
    
    inlines = [AssetTransferItemInline] # นำ Inline เข้ามาแสดงผล

    # จัดกลุ่มฟิลด์ให้ดูง่ายเหมือนหน้าฟอร์มกระดาษ
    fieldsets = (
        ('ส่วนที่ 1: ข้อมูลผู้ขอคำร้อง', {
            'fields': (
                'request_code', # เพิ่มรหัสคำร้องโชว์ไว้บนสุด
                'request_date', 
                'requester', 
                'department_name', 
                'status'
            )
        }),
        ('ส่วนที่ 2: ความเห็นหัวหน้างานพัสดุ', {
            'fields': ('head_approved', 'head_reject_reason', 'head_approver', 'head_action_date'),
            'classes': ('collapse',) # ซ่อนไว้เป็นแถบกดกางออกได้
        }),
        ('ส่วนที่ 3: การพิจารณาผู้อำนวยการ', {
            'fields': ('director_approved', 'director_reject_reason', 'director_approver', 'director_action_date'),
            'classes': ('collapse',)
        }),
        ('ส่วนที่ 4: การดำเนินการของเจ้าหน้าที่พัสดุ', {
            'fields': ('officer_action_status', 'officer_fail_reason', 'officer', 'officer_action_date'),
            'classes': ('collapse',)
        }),
    )