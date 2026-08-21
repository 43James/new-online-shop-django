from shop.models import MonthlyStockRecord
from orders.models import Order, OutOfStockNotification
from datetime import date

def stock_record_exists(request):
    today = date.today()
    
    # คำนวณเดือนที่แล้ว
    if today.month == 1:
        last_month = 12
        last_year = today.year - 1
    else:
        last_month = today.month - 1
        last_year = today.year

    # ตรวจสอบว่ามีข้อมูลอยู่หรือไม่
    exists = MonthlyStockRecord.objects.filter(month=last_month, year=last_year).exists()
    # print(f"Record exists for last month ({last_month}/{last_year}): {exists}")  # ควรพิมพ์ True ถ้ามีข้อมูล

    return {'stock_record_exists': exists}



def pending_outofstock(request):
    # นับจำนวนคำร้องที่ยังไม่ได้รับการรับทราบ
    pending_count = OutOfStockNotification.objects.filter(acknowledged=False).count()
    return {'pending_outofstock_count': pending_count}


def count_pending_orders(request):
    # ดึงข้อมูลออเดอร์ทั้งหมดที่รอการยืนยัน
    pending_orders = Order.objects.filter(status=None).count()
    return {'pending_orders_count': pending_orders}

def total_pending_actions(request):
    from django.db.models import Q
    count = Order.objects.filter(
        Q(status__isnull=True) | 
        Q(status=True, confirm=False)
    ).count()
    return {'total_pending_actions_count': count}

def asset_system_setting(request):
    try:
        from assets.models import AssetSystemSetting
        setting, created = AssetSystemSetting.objects.get_or_create(id=1)
        can_check = False
        if request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                can_check = True
            elif setting.is_public_check_enabled and setting.allowed_users.filter(id=request.user.id).exists():
                can_check = True
        return {'system_setting': setting, 'can_user_check_asset': can_check}
    except Exception:
        return {'system_setting': None}
