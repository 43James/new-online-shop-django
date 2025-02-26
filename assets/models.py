from django.db import models
from django.contrib.auth.models import User

# หมวดหมู่ครุภัณฑ์
class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="ชื่อหมวดหมู่")
    description = models.TextField(blank=True, null=True, verbose_name="รายละเอียดหมวดหมู่")

    def __str__(self):
        return self.name

# สถานที่ตั้งครุภัณฑ์
class Location(models.Model):
    name = models.CharField(max_length=255, verbose_name="ชื่อสถานที่")
    description = models.TextField(blank=True, null=True, verbose_name="รายละเอียดสถานที่")

    def __str__(self):
        return self.name

# ครุภัณฑ์
class Asset(models.Model):
    asset_code = models.CharField(max_length=50, unique=True, verbose_name="รหัสครุภัณฑ์")
    name = models.CharField(max_length=255, verbose_name="ชื่อครุภัณฑ์")
    description = models.TextField(blank=True, null=True, verbose_name="รายละเอียดครุภัณฑ์")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="หมวดหมู่ครุภัณฑ์")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, verbose_name="สถานที่ตั้งครุภัณฑ์")
    purchase_date = models.DateField(verbose_name="วันที่ซื้อ")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคาซื้อ")
    status = models.CharField(max_length=50, choices=[
        ('active', 'ใช้งานอยู่'),
        ('repair', 'ซ่อมแซม'),
        ('broken', 'เสีย'),
    ], default='active', verbose_name="สถานะการใช้งาน")
    image = models.ImageField(upload_to='asset_images/', blank=True, null=True, verbose_name="QR Code")
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True, verbose_name="รูปภาพครุภัณฑ์")

    def __str__(self):
        return self.name

# การครอบครองครุภัณฑ์
class AssetOwnership(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, verbose_name="ครุภัณฑ์")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้ครอบครอง")
    start_date = models.DateField(auto_now_add=True, verbose_name="วันที่เริ่มครอบครอง")
    end_date = models.DateField(blank=True, null=True, verbose_name="วันที่สิ้นสุดการครอบครอง")

    def __str__(self):
        return f"{self.user.username} - {self.asset.name}"

# การตรวจเช็คครุภัณฑ์
class AssetCheck(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, verbose_name="ครุภัณฑ์ที่ตรวจเช็ค")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้ตรวจเช็ค")
    check_date = models.DateField(auto_now_add=True, verbose_name="วันที่ตรวจเช็ค")
    status = models.CharField(max_length=50, choices=[
        ('pass', 'ผ่าน'),
        ('fail', 'ไม่ผ่าน'),
    ], verbose_name="สถานะการตรวจเช็ค")
    remarks = models.TextField(blank=True, null=True, verbose_name="หมายเหตุเพิ่มเติม")

    def __str__(self):
        return f"{self.asset.name} - {self.status}"

# การบันทึกการซ่อมบำรุง
class MaintenanceRecord(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, verbose_name="ครุภัณฑ์ที่ซ่อมบำรุง")
    maintenance_date = models.DateField(verbose_name="วันที่ซ่อมบำรุง")
    description = models.TextField(verbose_name="รายละเอียดการซ่อมบำรุง")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ค่าใช้จ่ายในการซ่อมบำรุง")

    def __str__(self):
        return f"{self.asset.name} - {self.maintenance_date}"

# การยืมและคืนครุภัณฑ์
class AssetLoan(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, verbose_name="ครุภัณฑ์ที่ยืม")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้ยืม")
    loan_date = models.DateField(auto_now_add=True, verbose_name="วันที่ยืม")
    return_date = models.DateField(blank=True, null=True, verbose_name="วันที่คืน")
    due_date = models.DateField(verbose_name="กำหนดคืน")
    status = models.CharField(
        max_length=20,
        choices=[('borrowed', 'กำลังยืม'), ('returned', 'คืนแล้ว'), ('overdue', 'เกินกำหนด')],
        default='borrowed',
        verbose_name="สถานะการยืม"
    )
    remarks = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")

    def __str__(self):
        return f"{self.asset.name} - {self.user.username} - {self.status}"

    def save(self, *args, **kwargs):
        # ตรวจสอบว่าวันที่คืนเกินกำหนดหรือไม่
        if self.return_date and self.return_date > self.due_date:
            self.status = 'overdue'
        elif self.return_date:
            self.status = 'returned'
        super().save(*args, **kwargs)
