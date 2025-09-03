# from django.db import models
# from django.contrib.auth.models import User

# # หมวดหมู่ครุภัณฑ์
# class Category(models.Model):
#     name = models.CharField(max_length=255, verbose_name="ชื่อหมวดหมู่")
#     description = models.TextField(blank=True, null=True, verbose_name="รายละเอียดหมวดหมู่")

#     def __str__(self):
#         return self.name

# # สถานที่ตั้งครุภัณฑ์
# class Location(models.Model):
#     name = models.CharField(max_length=255, verbose_name="ชื่อสถานที่")
#     description = models.TextField(blank=True, null=True, verbose_name="รายละเอียดสถานที่")

#     def __str__(self):
#         return self.name

# # ครุภัณฑ์
# class Asset(models.Model):
#     asset_code = models.CharField(max_length=50, unique=True, verbose_name="รหัสครุภัณฑ์")
#     name = models.CharField(max_length=255, verbose_name="ชื่อครุภัณฑ์")
#     description = models.TextField(blank=True, null=True, verbose_name="รายละเอียดครุภัณฑ์")
#     category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="หมวดหมู่ครุภัณฑ์")
#     location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, verbose_name="สถานที่ตั้งครุภัณฑ์")
#     purchase_date = models.DateField(verbose_name="วันที่ซื้อ")
#     purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคาซื้อ")
#     status = models.CharField(max_length=50, choices=[
#         ('active', 'ใช้งานอยู่'),
#         ('repair', 'ซ่อมแซม'),
#         ('broken', 'เสีย'),
#     ], default='active', verbose_name="สถานะการใช้งาน")
#     image = models.ImageField(upload_to='asset_images/', blank=True, null=True, verbose_name="QR Code")
#     qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True, verbose_name="รูปภาพครุภัณฑ์")

#     def __str__(self):
#         return self.name

# # การครอบครองครุภัณฑ์
# class AssetOwnership(models.Model):
#     asset = models.ForeignKey(Asset, on_delete=models.CASCADE, verbose_name="ครุภัณฑ์")
#     user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้ครอบครอง")
#     start_date = models.DateField(auto_now_add=True, verbose_name="วันที่เริ่มครอบครอง")
#     end_date = models.DateField(blank=True, null=True, verbose_name="วันที่สิ้นสุดการครอบครอง")

#     def __str__(self):
#         return f"{self.user.username} - {self.asset.name}"

# # การตรวจเช็คครุภัณฑ์
# class AssetCheck(models.Model):
#     asset = models.ForeignKey(Asset, on_delete=models.CASCADE, verbose_name="ครุภัณฑ์ที่ตรวจเช็ค")
#     user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้ตรวจเช็ค")
#     check_date = models.DateField(auto_now_add=True, verbose_name="วันที่ตรวจเช็ค")
#     status = models.CharField(max_length=50, choices=[
#         ('pass', 'ผ่าน'),
#         ('fail', 'ไม่ผ่าน'),
#     ], verbose_name="สถานะการตรวจเช็ค")
#     remarks = models.TextField(blank=True, null=True, verbose_name="หมายเหตุเพิ่มเติม")

#     def __str__(self):
#         return f"{self.asset.name} - {self.status}"

# # การบันทึกการซ่อมบำรุง
# class MaintenanceRecord(models.Model):
#     asset = models.ForeignKey(Asset, on_delete=models.CASCADE, verbose_name="ครุภัณฑ์ที่ซ่อมบำรุง")
#     maintenance_date = models.DateField(verbose_name="วันที่ซ่อมบำรุง")
#     description = models.TextField(verbose_name="รายละเอียดการซ่อมบำรุง")
#     cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ค่าใช้จ่ายในการซ่อมบำรุง")

#     def __str__(self):
#         return f"{self.asset.name} - {self.maintenance_date}"

# # การยืมและคืนครุภัณฑ์
# class AssetLoan(models.Model):
#     asset = models.ForeignKey(Asset, on_delete=models.CASCADE, verbose_name="ครุภัณฑ์ที่ยืม")
#     user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้ยืม")
#     loan_date = models.DateField(auto_now_add=True, verbose_name="วันที่ยืม")
#     return_date = models.DateField(blank=True, null=True, verbose_name="วันที่คืน")
#     due_date = models.DateField(verbose_name="กำหนดคืน")
#     status = models.CharField(
#         max_length=20,
#         choices=[('borrowed', 'กำลังยืม'), ('returned', 'คืนแล้ว'), ('overdue', 'เกินกำหนด')],
#         default='borrowed',
#         verbose_name="สถานะการยืม"
#     )
#     remarks = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")

#     def __str__(self):
#         return f"{self.asset.name} - {self.user.username} - {self.status}"

#     def save(self, *args, **kwargs):
#         # ตรวจสอบว่าวันที่คืนเกินกำหนดหรือไม่
#         if self.return_date and self.return_date > self.due_date:
#             self.status = 'overdue'
#         elif self.return_date:
#             self.status = 'returned'
#         super().save(*args, **kwargs)



from django.utils import timezone
from django.db import models
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from accounts.models import MyUser


# หมวดหมู่หลัก
class AssetCategory(models.Model):
    name_cate = models.CharField(max_length=100, verbose_name='หมวดหมู่หลัก')

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.name_cate

# หมวดหมู่ย่อย
class Subcategory(models.Model):
    name_sub = models.CharField(max_length=100, verbose_name='หมวดหมู่ย่อย')
    category = models.ForeignKey(AssetCategory, on_delete=models.CASCADE, related_name='subcategories', verbose_name='หมวดหมู่หลัก')

    class Meta: 
        ordering = ('id',)

    def __str__(self):
        return self.name_sub

# สถานที่เก็บครุภัณฑ์
class StorageLocation(models.Model):
    name = models.CharField(max_length=255, verbose_name="สถานที่เก็บ")

    def __str__(self):
        return self.name

# รหัสครุภัณฑ์
class AssetCode(models.Model):
    asset_type = models.CharField(max_length=5, verbose_name="ประเภท")
    asset_kind = models.CharField(max_length=5, verbose_name="ชนิด")
    asset_character = models.CharField(max_length=5, verbose_name="ลักษณะ")
    serial_year = models.CharField(max_length=10, verbose_name="ลำดับ/ปี", unique=True) # เพิ่ม unique=True ที่นี่

    # class Meta:
    #     unique_together = ('asset_type', 'asset_kind', 'asset_character', 'serial_year')

    def __str__(self):
        return f"{self.asset_type}-{self.asset_kind}-{self.asset_character}-{self.serial_year}"

# รายการครุภัณฑ์
class AssetItem(models.Model):
    DAMAGE_STATUS_CHOICES = [
        ('ชำรุด', 'ชำรุด'),
        ('เสื่อม', 'เสื่อม'),
        ('สูญไป', 'สูญไป'),
        ('ไม่ใช้', 'ไม่ใช้'),
        ('ใช้อยู่', 'ใช้อยู่'),
    ]
    item_name = models.CharField(max_length=255, verbose_name="ชื่อรายการครุภัณฑ์")
    # category = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='Subcategory', null=True, blank=True, verbose_name='หมวดหมู่')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='asset_items', null=True, blank=True, verbose_name='หมวดหมู่')
    asset_code = models.ForeignKey(AssetCode, on_delete=models.CASCADE, verbose_name="รหัสครุภัณฑ์")
    # quantity = models.IntegerField(verbose_name="จำนวน")
    unit = models.CharField(max_length=50, verbose_name="หน่วยนับ")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคาที่ซื้อ")
    date_asset_created = models.DateTimeField(auto_now_add=True, verbose_name='วันที่เพิ่มข้อมูล')
    date_asset_updated = models.DateTimeField(auto_now=True, verbose_name='วันที่อัพเดทข้อมูล')
    purchase_date = models.DateField(verbose_name="วันที่ซื้อ")
    fiscal_year = models.IntegerField(verbose_name="ปีที่ใช้งาน")
    lifetime = models.IntegerField(verbose_name="อายุการใช้งาน (ปี)")
    used_years = models.IntegerField(verbose_name="ใช้มาแล้วกี่ปี")
    annual_depreciation = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ค่าความเสื่อมต่อปี")
    responsible_person = models.CharField(max_length=255, verbose_name="ผู้รับผิดชอบดูแลกำกับ")
    storage_location = models.ForeignKey(StorageLocation, on_delete=models.CASCADE, verbose_name="สถานที่เก็บ")
    brand_model = models.CharField(max_length=255, verbose_name="ยี่ห้อ/รุ่น")
    notes = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")
    damage_status = models.CharField(max_length=10, choices=DAMAGE_STATUS_CHOICES, verbose_name="สถานะการใช้งาน")
    status_borrowing = models.BooleanField(default=False, verbose_name="ครุภัณฑ์ที่ยืมได้")
    status_assetloan = models.BooleanField(default=False, verbose_name="สถานะการยืม")
    asset_image = models.ImageField(upload_to="assets/", blank=True, null=True, verbose_name="รูปภาพครุภัณฑ์") # เพิ่มฟิลด์รูปภาพครุภัณฑ์    
    qr_code = models.ImageField(upload_to="qrcodes/", blank=True, null=True, verbose_name="QR Code") # เพิ่มฟิลด์ QR Code

    class Meta:
        verbose_name = "ครุภัณฑ์"
        verbose_name_plural = "รายการครุภัณฑ์"

    def __str__(self):
        return f"{self.asset_code} - {self.item_name}"

    def generate_qr_code(self):
        """ ฟังก์ชันสร้าง QR Code อัตโนมัติจากรหัสครุภัณฑ์ """
        qr_data = f"{settings.SITE_URL}/asset/{self.id}/"
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        filename = f"qrcode_{self.asset_code.id}.png"
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)

    def calculate_annual_depreciation(self):
        """ คำนวณค่าความเสื่อมต่อปี = ราคาที่ซื้อ / อายุการใช้งาน """
        if self.lifetime > 0:
            return self.purchase_price / self.lifetime
        return 0

    def save(self, *args, **kwargs):
        """ บันทึกค่าความเสื่อมต่อปีโดยอัตโนมัติ และสร้าง QR Code """
        # คำนวณค่าความเสื่อมก่อนบันทึก
        if self.subcategory and self.subcategory.name_sub == "ต่ำกว่าเกณฑ์":
            self.annual_depreciation = 0
        else:
            self.annual_depreciation = self.calculate_annual_depreciation()
        
        # บันทึกข้อมูลครั้งแรกเพื่อให้ได้ self.id
        super().save(*args, **kwargs)
        
        # สร้างและบันทึก QR Code หลังจากที่บันทึกข้อมูลแล้ว
        if not self.qr_code: # ตรวจสอบว่ายังไม่มี QR Code ก่อนสร้าง
            self.generate_qr_code()
            super().save(update_fields=['qr_code']) # บันทึกเฉพาะฟิลด์ qr_code


# การครอบครองครุภัณฑ์
class AssetOwnership(models.Model):
    asset = models.ForeignKey(AssetItem, on_delete=models.CASCADE, verbose_name="ครุภัณฑ์")
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, verbose_name="ผู้ครอบครอง")
    start_date = models.DateField(blank=True, null=True, verbose_name="วันที่เริ่มครอบครอง")
    end_date = models.DateField(blank=True, null=True, verbose_name="วันที่สิ้นสุดการครอบครอง")

    def __str__(self):
        return f"{self.user.username} - {self.asset.item_name}"


# การตรวจเช็คครุภัณฑ์
class AssetCheck(models.Model):
    asset = models.ForeignKey(AssetItem, on_delete=models.CASCADE, verbose_name="ครุภัณฑ์ที่ตรวจเช็ค")
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, verbose_name="ผู้ตรวจเช็ค")
    check_date = models.DateField(auto_now_add=True, verbose_name="วันที่ตรวจเช็ค")
    status = models.BooleanField(default=False, verbose_name="สถานะการตรวจเช็ค")  # กำหนดค่าเริ่มต้น
    remarks = models.TextField(blank=True, null=True, verbose_name="หมายเหตุเพิ่มเติม")
    month = models.PositiveIntegerField(verbose_name="เดือนที่บันทึก", editable=False)
    year = models.PositiveIntegerField(verbose_name="ปีงบประมาณ", editable=False)

    def __str__(self):
        return f"{self.asset.item_name} - {'ตรวจแล้ว' if self.status else 'ยังไม่ตรวจ'}"

    def save(self, *args, **kwargs):
        # กำหนดเดือนและปีจากวันที่ตรวจเช็ค
        if not self.check_date:
            self.check_date = timezone.now().date()
        
        self.month = self.check_date.month
        self.year = self.check_date.year
        super().save(*args, **kwargs)

# ออเดอร์การยืมครุภัณฑ์
class OrderAssetLoan(models.Model):
    STATUS_CHOICES_LOAN = [
        ('pending', 'รออนุมัติ'),
        ('approved', 'อนุมัติแล้ว'),
        ('rejected', 'ปฏิเสธ'),
        ('borrowed', 'กำลังยืม'),
        ('returned_pending', 'รออนุมัติการคืน'),
        ('returned', 'คืนแล้ว'),
        ('overdue', 'เกินกำหนด'),
    ]

    STATUS_CHOICES_RETURN = [
        ('damaged', 'ชำรุด'),
        ('not_damaged', 'ไม่มีรายการชำรุด'),
    ]

    # ข้อมูลทั่วไป
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='asset_loans', verbose_name='ผู้ยืมครุภัณฑ์')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='วันที่สร้างออเดอร์')
    date_of_use = models.DateTimeField(blank=True, null=True, verbose_name="วันที่ใช้")
    date_due = models.DateTimeField(verbose_name="กำหนดคืน")
    date_of_return = models.DateTimeField(blank=True, null=True, verbose_name="วันที่คืนจริง")
    date_updated = models.DateTimeField(auto_now=True, verbose_name='อัพเดทล่าสุด')

    # สถานะออเดอร์
    status = models.CharField(max_length=20, choices=STATUS_CHOICES_LOAN, default='pending', verbose_name="สถานะการยืม")
    note = models.TextField(blank=True, null=True, verbose_name='หมายเหตุ')

    # ฝั่งเจ้าหน้าที่อนุมัติ
    approved_by = models.CharField(max_length=100, blank=True, null=True, verbose_name='ชื่อเจ้าหน้าที่อนุมัติ')
    approver_position = models.CharField(max_length=100, blank=True, null=True, verbose_name='ตำแหน่งเจ้าหน้าที่อนุมัติ')
    date_approved = models.DateTimeField(blank=True, null=True, verbose_name="วันที่อนุมัติ")

    # ฝั่งผู้ยืมส่งคืน
    returned_by = models.CharField(max_length=100, blank=True, null=True, verbose_name='ชื่อผู้คืนครุภัณฑ์')
    date_returned = models.DateTimeField(blank=True, null=True, verbose_name="วันที่คืน")

    # ฝั่งเจ้าหน้าที่รับคืน
    status_return = models.CharField(max_length=20, choices=STATUS_CHOICES_RETURN, default='not_damaged', verbose_name="สถานะการคืน")
    received_by = models.CharField(max_length=100, blank=True, null=True, verbose_name='ชื่อเจ้าหน้าที่รับคืน')
    receiver_position = models.CharField(max_length=100, blank=True, null=True, verbose_name='ตำแหน่งเจ้าหน้าที่รับคืน')
    confirm_received = models.BooleanField(default=False, verbose_name="ยืนยันการรับคืน")
    receiver_note = models.TextField(blank=True, null=True, verbose_name='ความคิดเห็นเจ้าหน้าที่รับคืน')
    date_received = models.DateTimeField(blank=True, null=True, verbose_name="วันที่บันทึกรับคืน")

    # สำหรับสรุปรายเดือน/รายปี
    month = models.PositiveIntegerField(verbose_name='เดือน', editable=False, default=timezone.now().month)
    year = models.PositiveIntegerField(verbose_name='ปี', editable=False, default=timezone.now().year)

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return f"Order #{self.id} - {self.user}"

    @property
    def get_pending_approval_count(self):
        """นับจำนวนออเดอร์ที่ยังรออนุมัติ"""
        return OrderAssetLoan.objects.filter(status='pending').count()

    @property
    def get_total_assets(self):
        """นับจำนวนครุภัณฑ์ทั้งหมดในออเดอร์"""
        return self.items.count()
    
    @property
    def get_approver_first_name(self):
        if self.approved_by:
            return self.approved_by.split(' ')[1]
        return None

    @property
    def get_approver_last_name(self):
        if self.approved_by and ' ' in self.approved_by:
            return self.approved_by.split(' ')[2]
        return None
    
    @property
    def get_received_by_first_name(self):
        if self.received_by:
            return self.received_by.split(' ')[1]
        return None

    @property
    def get_returned_by_first_name(self):
        if self.returned_by:
            return self.returned_by.split(' ')[1]
        return None

    def save(self, *args, **kwargs):
        # เซ็ตเดือน/ปีตอนสร้าง
        if not self.id:
            now = timezone.now()
            self.month = now.month
            self.year = now.year

        # ตรวจสอบสถานะเมื่อมีการคืน
        if self.date_of_return:
            if self.date_of_return > self.date_due:
                self.status = 'overdue'
            else:
                self.status = 'returned'

        super().save(*args, **kwargs)


# รายการครุภัณฑ์ที่ผูกกับออเดอร์
class IssuingAssetLoan(models.Model):
    order_asset = models.ForeignKey(OrderAssetLoan, on_delete=models.CASCADE, related_name='items', verbose_name='ออเดอร์')
    asset = models.ForeignKey(AssetItem, on_delete=models.CASCADE, related_name='issued_loans', verbose_name="ครุภัณฑ์ที่ยืม")
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='วันที่ทำรายการ')
    month = models.PositiveIntegerField(verbose_name='เดือน', editable=False, default=timezone.now().month)
    year = models.PositiveIntegerField(verbose_name='ปี', editable=False, default=timezone.now().year)

    def __str__(self):
        return f"Issue #{self.id} - {self.asset}"

    def save(self, *args, **kwargs):
        if not self.id:  # ถ้าเพิ่งสร้างใหม่
            now = timezone.now()
            self.month = now.month
            self.year = now.year
        super().save(*args, **kwargs)




# # การยืมและคืนครุภัณฑ์
# class AssetLoan(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'รออนุมัติ'),
#         ('approved', 'อนุมัติแล้ว'),
#         ('rejected', 'ปฏิเสธ'),
#         ('borrowed', 'กำลังยืม'),
#         ('returned_pending', 'รออนุมัติการคืน'),
#         ('returned', 'คืนแล้ว'),
#         ('overdue', 'เกินกำหนด'),
#     ]
#     asset = models.ForeignKey(AssetItem, on_delete=models.CASCADE, verbose_name="ครุภัณฑ์ที่ยืม")
#     user = models.ForeignKey(MyUser, on_delete=models.CASCADE, verbose_name="ผู้ยืม")
#     loan_date = models.DateField(auto_now_add=True, verbose_name="วันที่ยืม")
#     date_of_use = models.DateField(blank=True, null=True, verbose_name="วันที่ใช้")
#     date_of_return = models.DateField(blank=True, null=True, verbose_name="วันที่คืน")
#     date_due = models.DateField(verbose_name="กำหนดคืน")
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="สถานะ")
#     date_received = models.DateTimeField(blank=True, null=True, verbose_name='วันที่รับ')
#     confirm = models.BooleanField(default=False, verbose_name="ยืนยันรับครุภัณฑ์")
#     remarks = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")

#     def __str__(self):
#         return f"{self.asset.item_name} - {self.user.username} - {self.status}"

#     def save(self, *args, **kwargs):
#         # ตรวจสอบว่าวันที่คืนเกินกำหนดหรือไม่
#         if self.date_of_return and self.date_of_return > self.date_due:
#             self.status = 'overdue'
#         elif self.date_of_return:
#             self.status = 'returned'
#         super().save(*args, **kwargs)




# การบันทึกการซ่อมบำรุง
# class MaintenanceRecord(models.Model):
#     asset = models.ForeignKey(AssetItem, on_delete=models.CASCADE, verbose_name="ครุภัณฑ์ที่ซ่อมบำรุง")
#     maintenance_date = models.DateField(verbose_name="วันที่ซ่อมบำรุง")
#     Notification_date = models.DateField(verbose_name="วันที่แจ้ง")
#     Completion_date = models.DateField(verbose_name="วันที่เสร็จ")
#     description = models.TextField(verbose_name="รายละเอียดการซ่อมบำรุง ความเห็น หลักฐาน")
#     cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ค่าใช้จ่ายในการซ่อมบำรุง")

#     def __str__(self):
#         return f"{self.asset.item_name} - {self.maintenance_date}"


