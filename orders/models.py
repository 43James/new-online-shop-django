# from datetime import timezone
from django.utils import timezone
from django.db import models
from accounts.models import MyUser
from shop.models import Product, Receiving
from django.core.validators import MinValueValidator


class Order(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='orders', verbose_name='ผู้ใช้ID')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='วันที่ทำรายการ')
    date_updated = models.DateTimeField(auto_now=True, verbose_name='วันที่อัพเดทออเดอร์')
    status = models.BooleanField(blank=True, null=True,verbose_name="สถานะออเดอร์")
    pay_item = models.BooleanField(default=False, verbose_name="ยืนยันจ่ายวัสดุ")
    name_pay = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='ชื่อผู้จ่าย')
    surname_pay = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='นามสกุลผู้จ่าย')
    confirm = models.BooleanField(default=False, verbose_name="ยืนยันรับพัสดุ")
    name_sign = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='ชื่อผู้รับวัสดุ')
    other = models.CharField(max_length=500 ,blank=True, null=True, verbose_name='หมายเหตุ')
    date_receive = models.DateTimeField(blank=True, null=True, verbose_name='วันที่นัดรับพัสดุ')
    date_received = models.DateTimeField(blank=True, null=True, verbose_name='วันที่ได้รับพัสดุ')
    date_approved = models.DateTimeField(blank=True, null=True, verbose_name='วันที่อนุมัติ')
    month = models.PositiveIntegerField(verbose_name='เดือน', editable=False, default=timezone.now().month)
    year = models.PositiveIntegerField(verbose_name='ปี', editable=False, default=timezone.now().year)

    class Meta:
        ordering = ('-id',)
    
    def __str__(self):
        return str(self.id)

    @property
    def get_approval_count(self):
        return Order.objects.filter(approve=False).count()

    @property
    def get_total_price(self):
        total = sum(item.get_cost() for item in self.items.all())
        return total
    
    @property
    def get_total_sum(self):
        total = sum(item.get_total() for item in self.items.all())
        return total
    
    def save(self, *args, **kwargs):
        if not self.id:  # ตรวจสอบว่าเป็นการบันทึกครั้งแรกหรือไม่
            now = timezone.now()
            self.month = now.month
            self.year = now.year
        super().save(*args, **kwargs)

    
class Issuing(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='ออเดอร์ที่')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='Issuing', verbose_name='สินค้า')
    receiving = models.ForeignKey(Receiving, on_delete=models.CASCADE, related_name='issuings', verbose_name='รายการรับเข้า')  # ใช้ ForeignKey
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], verbose_name='ราคา')
    quantity = models.SmallIntegerField(verbose_name='จำนวน')
    note = models.CharField(max_length=500 ,blank=True, null=True, verbose_name='หมายเหตุ')
    datecreated = models.DateTimeField(auto_now_add=True, verbose_name='วันที่ทำรายการ')
    month = models.PositiveIntegerField(verbose_name='เดือน', editable=False, default=timezone.now().month)
    year = models.PositiveIntegerField(verbose_name='ปี', editable=False, default=timezone.now().year)
    
    
    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity
    
    def get_total(self):
        return self.quantity
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.id:  # ตรวจสอบว่าเป็นการบันทึกครั้งแรกหรือไม่
            now = timezone.now()
            self.month = now.month
            self.year = now.year
        super().save(*args, **kwargs)

    # def save(self, *args, **kwargs):
    #     if not self.id:  # ตรวจสอบว่าเป็นการบันทึกครั้งแรกหรือไม่
    #         self.month = self.datecreated.month if self.datecreated else timezone.now().month
    #         self.year = self.datecreated.year if self.datecreated else timezone.now().year
    #     super().save(*args, **kwargs)

    # @classmethod
    # def filter_by_month_year(cls, month, year):
    #     # แปลงเดือนและปีเป็นเดือนและปีที่ใช้ในฐานข้อมูล
    #     month = int(month)
    #     year_buddhist = int(year) + 543
    #     year_ad = year_buddhist - 543
        
    #     # คิวรี่ข้อมูลในฐานข้อมูลตามเดือนและปีที่ระบุ
    #     return cls.objects.filter(datecreated__month=month, datecreated__year=year_ad)



# class Approvereport(models.Model):
#     month_report = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='รายงานการเบิกวัสดุประจำเดือน')

#     name_sign1 = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='ชื่อ ผู้สำรวจ1')
#     surname_sign1 = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='นามสกุล ผู้สำรวจ1')
#     position1 = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='ตำแหน่ง1')

#     name_sign2 = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='ชื่อ ผู้สำรวจ2')
#     surname_sign2 = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='นามสกุล ผู้สำรวจ2')
#     position2 = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='ตำแหน่ง2')

#     approve = models.BooleanField(default=False, verbose_name="อนุมัติรายงาน")
#     name_approve = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='ชื่อ ผู้ตรวจสอบ')
#     surname_approve = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='นามสกุล ผู้ตรวจสอบ')
#     position3 = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='ตำแหน่ง3')
#     other = models.CharField(max_length=500 ,blank=True, null=True, verbose_name='หมายเหตุ')

#     month = models.PositiveIntegerField(verbose_name='เดือน', editable=False, default=timezone.now().month)
#     year = models.PositiveIntegerField(verbose_name='ปี', editable=False, default=timezone.now().year)

#     date_created = models.DateTimeField(auto_now_add=True, verbose_name='วันที่ทำรายการ')
#     date_updated = models.DateTimeField(auto_now=True, verbose_name='วันที่อัพเดท')

#     class Meta:
#         ordering = ('-id',)
    
#     def __str__(self):
#         return str(self.id)
    
#     def save(self, *args, **kwargs):
#         if not self.id:  # ตรวจสอบว่าเป็นการบันทึกครั้งแรกหรือไม่
#             now = timezone.now()
#             self.month = now.month
#             self.year = now.year
#         super().save(*args, **kwargs)



# แจ้งเตือนวัสดุหมด
class OutOfStockNotification(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, verbose_name='ผู้แจ้ง', related_name='notifications')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='วัสดุ', related_name='notifications')
    quantity_requested = models.PositiveIntegerField(verbose_name='จำนวนที่ต้องการเพิ่ม')
    note = models.TextField(blank=True, null=True, verbose_name='หมายเหตุ')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='วันที่แจ้ง')
    acknowledged = models.BooleanField(default=False, verbose_name='รับทราบ')
    restocked = models.BooleanField(default=False, verbose_name='เติมสต๊อกแล้ว')
    acknowledged_note = models.TextField(blank=True, null=True, verbose_name='โน๊ตจากเจ้าหน้าที่')

    class Meta:
        ordering = ['-date_created']
        verbose_name = "การแจ้งวัสดุหมด"
        verbose_name_plural = "การแจ้งวัสดุหมด"

    def __str__(self):
        return f"แจ้ง {self.product} โดย {self.user.get_full_name()}"

    def get_user_full_name(self):
        return self.user.get_full_name()