from django.db import models
from accounts.models import MyUser
from shop.models import Product, Receiving


class Order(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='orders', verbose_name='ผู้ใช้ID')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='วันที่ทำรายการ')
    date_updated = models.DateTimeField(auto_now=True, verbose_name='วันที่อัพเดทออเดอร์')
    status = models.BooleanField(blank=True, null=True,verbose_name="สถานะออเดอร์")
    date_receive = models.DateTimeField(blank=True, null=True, verbose_name='วันที่จ่ายพัสดุ')
    other = models.CharField(max_length=50 ,blank=True, null=True, verbose_name='หมายเหตุ')

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

    
class Issuing(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='ออเดอร์ที่')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='Issuing', verbose_name='สินค้า')
    receiving = models.ForeignKey(Receiving, on_delete=models.CASCADE, related_name='issuings', verbose_name='รายการรับเข้า')  # ใช้ ForeignKey
    price = models.PositiveIntegerField(verbose_name='ราคา')
    quantity = models.SmallIntegerField(verbose_name='จำนวน')
    datecreated = models.DateTimeField(auto_now_add=True, verbose_name='วันที่ทำรายการ')

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity
    
    def get_total(self):
        return self.quantity
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)