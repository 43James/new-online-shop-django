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
    confirm = models.BooleanField(default=False, verbose_name="ยืนยันรับพัสดุ")
    pay_item = models.BooleanField(default=False, verbose_name="ยืนยันจ่ายวัสดุ")
    date_receive = models.DateTimeField(blank=True, null=True, verbose_name='วันที่นัดรับพัสดุ')
    date_received = models.DateTimeField(blank=True, null=True, verbose_name='วันที่ได้รับพัสดุ')
    name_sign = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='ชื่อผู้รับวัสดุ')
    other = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='หมายเหตุ')
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
            self.month = self.month
            self.year = self.year
        super().save(*args, **kwargs)

    
class Issuing(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='ออเดอร์ที่')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='Issuing', verbose_name='สินค้า')
    receiving = models.ForeignKey(Receiving, on_delete=models.CASCADE, related_name='issuings', verbose_name='รายการรับเข้า')  # ใช้ ForeignKey
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], verbose_name='ราคา')
    quantity = models.SmallIntegerField(verbose_name='จำนวน')
    note = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='หมายเหตุ')
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