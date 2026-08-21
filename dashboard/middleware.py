from datetime import datetime, timedelta
import threading
from django.db.models import Sum, F, DecimalField
from shop.models import Product, Receiving, MonthlyStockRecord

stock_record_lock = threading.Lock()

def run_auto_stock_recording(month, year):
    # Check if already recorded to avoid race conditions
    with stock_record_lock:
        if MonthlyStockRecord.objects.filter(month=month, year=year).exists():
            return
            
        products = Product.objects.all()
        records = []
    
    for product in products:
        receiving_data = Receiving.objects.filter(
            product=product,
        ).aggregate(
            total_quantity_received=Sum('quantity'),
            total_remaining_value=Sum(F('quantity') * F('unitprice'), output_field=DecimalField())
        )

        total_quantity_received = receiving_data['total_quantity_received'] or 0
        total_price = receiving_data['total_remaining_value'] or 0.00

        records.append(MonthlyStockRecord(
            product=product,
            month=month,
            year=year,
            end_of_month_balance=total_quantity_received,
            total_price=total_price
        ))
        
    MonthlyStockRecord.objects.bulk_create(records)

class AutoMonthlyStockMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        now = datetime.now()
        
        # ถ้านี่คือวันที่ 1 ของเดือน ให้ทำการเช็คและบันทึกสต็อกของเดือนก่อนหน้า
        if now.day == 1:
            first_day_of_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
            
            month = last_day_of_previous_month.month
            year = last_day_of_previous_month.year
            
            if not MonthlyStockRecord.objects.filter(month=month, year=year).exists():
                # รันบน Background Thread เพื่อไม่ให้หน้าเว็บโหลดช้า
                t = threading.Thread(target=run_auto_stock_recording, args=(month, year))
                t.start()

        response = self.get_response(request)
        return response
