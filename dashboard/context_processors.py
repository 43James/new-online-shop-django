from shop.models import MonthlyStockRecord
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
