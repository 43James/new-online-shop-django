from django.utils import timezone
from django.db import models
from django.urls import reverse
from django.template.defaultfilters import slugify
from django.db.models import Sum
from django.utils.html import format_html
from django.core.validators import MinValueValidator

# from orders.models import Issuing


class Category(models.Model):
    name_cate = models.CharField(max_length=100,verbose_name='หมวดหมู่หลัก')

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return self.name_cate
    
class Subcategory(models.Model):
    name_sub = models.CharField(max_length=100, verbose_name='หมวดหมู่ย่อย')
    category = models.ForeignKey(Category, on_delete=models.CASCADE,related_name='category', verbose_name='หมวดหมู่หลัก')
    
    class Meta:
        ordering = ('-id',)
        
    def __str__(self):
        return self.name_sub
    
        
class Product(models.Model):
    category = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='Subcategory', null=True, blank=True, verbose_name='หมวดหมู่')
    image = models.ImageField(upload_to='products', null=True, blank=True, verbose_name='รูปภาพ')
    product_id = models.CharField(max_length=50, unique=True, verbose_name='รหัสพัสดุ')
    # slug = models.SlugField(max_length=50, unique=True)
    product_name = models.CharField(max_length=200, verbose_name='ชื่อรายการ')
    description = models.TextField(verbose_name='คำอธิบาย')
    quantityinstock = models.PositiveIntegerField(default=0, null=True, verbose_name='จำนวนที่มีในสต๊อก')
    # unitprice = models.PositiveIntegerField(default=0, null=True, verbose_name='ราคา/หน่วย')
    unit = models.CharField(max_length=20, verbose_name='หน่วย')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='วันที่เพิ่มรายการ')
    date_updated = models.DateTimeField(auto_now=True, verbose_name='วันที่อัพเดตข้อมูล')


    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.product_id
    
    def img(self):
        if self.image:
            return format_html('<img src="' + self.image.url + '" height="50px">')
        return ''
    image.allow_tags = True
        
    def get_absolute_url(self):
        return reverse('shop:product_detail', kwargs={'product_id': self.product_id})

    
class Suppliers(models.Model):
    supname = models.CharField(max_length=50, verbose_name='ชื่อบริษัท')
    contactname = models.CharField(max_length=60, verbose_name='ชื่อผู้ติดต่อ')
    phone = models.CharField(max_length=10, verbose_name='เบอร์โทรศัพท์')
    address = models.CharField(max_length=255, verbose_name='ที่อยู่')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='วันที่เพิ่มรายการ')

    class Meta:
        ordering = ('-id',)
    
    def __str__(self):
        return str(self.id)
    
    
class MonthlyStockRecord(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='monthly_stock_records', verbose_name='IDสินค้า')
    month = models.IntegerField(null=True, blank=True, verbose_name='เดือน')
    year = models.IntegerField(null=True, blank=True, verbose_name='ปี')
    end_of_month_balance = models.PositiveIntegerField(null=True, blank=True, verbose_name='จำนวนคงเหลือ')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='ราคารวม')
    date_recorded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.product_name} - {self.month}/{self.year}"
    

class Receiving(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='Receiving', verbose_name='IDสินค้า')
    suppliers = models.ForeignKey(Suppliers, on_delete=models.CASCADE, related_name='suppliers', verbose_name='IDซัพพลายเออร์')
    quantityreceived = models.PositiveIntegerField(null=True,  verbose_name='จำนวนที่รับเข้า')
    quantity = models.PositiveIntegerField( null=True, verbose_name='จำนวนคงเหลือ')
    unitprice = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], null=True, verbose_name='ราคา/หน่วย')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='วันที่เพิ่มรายการ')
    date_received = models.DateTimeField(blank=True, null=True, verbose_name='วันที่รับเข้า')
    date_updated = models.DateTimeField(auto_now=True, verbose_name='วันที่อัพเดตข้อมูล')
    month = models.PositiveIntegerField(verbose_name='เดือนที่รับเข้า', editable=False, default=timezone.now().month)
    year = models.PositiveIntegerField(verbose_name='ปีที่รับเข้า', editable=False, default=timezone.now().year)

    class Meta:
        ordering = ('-id',)
    
    def __str__(self):
        return str(self.product)
    
    def save(self, *args, **kwargs):
        if not self.id:  # ตรวจสอบว่าเป็นการบันทึกครั้งแรกหรือไม่
            self.month = self.month
            self.year = self.year
        super().save(*args, **kwargs)
    
    @staticmethod
    def total_quantity_by_product(product_id):
        result = Receiving.objects.filter(product_id=product_id).aggregate(total_quantity=Sum('quantity'))
        return result['total_quantity'] or 0
    
    def get_absolute_url(self):
        return reverse('shop:product_detail', kwargs={'id':self.id})
        # return reverse('shop:product_detail', kwargs={'slug': self.product.slug})

    # @property
    # def total_quantity(self):
    #     return Receiving.objects.filter(product=self.product).aggregate(total_quantity=Sum('quantityreceived'))['total_quantity'] or 0
    
    # @property
    # def total_price(self):
    #     total_price = Receiving.objects.filter(product=self.product).aggregate(
    #         total_price=Sum(F('quantityreceived') * F('unitprice'))
    #     )['total_price']
    #     return total_price or 0


class Total_Quantity(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='IDสินค้า')
    totalquantity = models.PositiveIntegerField(default=0)  # จำนวนสินค้าทั้งหมด

    class Meta:
        ordering = ('-id',)
    
    def __str__(self):
        return str(self.id)
    

class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='IDสินค้า')
    quantity = models.PositiveIntegerField(default=0)  # จำนวนสินค้าในสต็อก

    class Meta:
        ordering = ('-id',)
    
    def __str__(self):
        return str(self.product)


class TotalQuantity(models.Model):
    receiving = models.ForeignKey(Receiving, on_delete=models.CASCADE, related_name='receiving', verbose_name='IDสินค้า')
    total_quantity = models.PositiveIntegerField(null=True , verbose_name='รวมจำนวนที่รับเข้าทั้งหมด')  # จำนวนสินค้าทั้งหมด

    class Meta:
        ordering = ('-id',)
    
    def __str__(self):
        return str(self.id)
    
    def calculate_total_quantity(self):
        total = 0
        # คำนวณจำนวนสินค้าทั้งหมดจากการรับเข้าทั้งหมดในรายการ receiving นี้
        receiving_items = Receiving.objects.filter(receiving=self.receiving)
        for item in receiving_items:
            total += item.quantityreceived
        return total
    

    