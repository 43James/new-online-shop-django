# from django_cron import CronJobBase, Schedule
# from shop.views import record_monthly_stock

# class RecordMonthlyStockCronJob(CronJobBase):
#     RUN_AT_TIMES = ['18:00']  # ตั้งเวลาให้รันตอนเที่ยงคืนของวันที่ 30 หรือ 31

#     schedule = Schedule(run_at_times=RUN_AT_TIMES)
#     code = 'shop.cron.RecordMonthlyStockCronJob'  # ใส่ชื่อที่ไม่ซ้ำกันสำหรับ Cron Job นี้

#     def do(self):
#         record_monthly_stock()
        
        
        
        
# class RecordMonthlyStockCronJob(CronJobBase):
#     RUN_AT_TIMES = ['18:00']

#     schedule = Schedule(
#         run_at_times=RUN_AT_TIMES,
#         # Set to run at the last day of each month
#         month="*",
#         day_of_month="last",
#         hour="23",
#         minute="59"
#     )
#     code = 'shop.record_monthly_stock_cron_job'    # a unique code

#     def do(self):
#         record_monthly_stock()
#         print("Monthly stock record cron job executed successfully")
