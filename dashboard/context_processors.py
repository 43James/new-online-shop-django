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