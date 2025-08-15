from django import forms
from .models import AssetCheck, AssetCode, AssetItem, AssetLoan, AssetOwnership, StorageLocation, AssetCategory, Subcategory, StorageLocation


class AssetCodeForm(forms.ModelForm):
    class Meta:
        model = AssetCode
        fields = ["asset_type", "asset_kind", "asset_character", "serial_year"]
        labels = {
            "asset_type": "ประเภท",
            "asset_kind": "ชนิด",
            "asset_character": "ลักษณะ",
            "serial_year": "ลำดับ/ปี",
        }

class AssetItemForm(forms.ModelForm):
    class Meta:
        model = AssetItem
        fields = [
            "item_name", "subcategory",
            "quantity", "unit", "purchase_price", "purchase_date", 
            "fiscal_year", "lifetime", "used_years", 
            "responsible_person", "storage_location", 
            "brand_model", "damage_status", "notes", "asset_image",
            "status_borrowing", "status_assetloan", # ✅ เพิ่ม 2 ฟิลด์นี้
        ]
        labels = {
            "item_name": "ชื่อรายการครุภัณฑ์",
            "subcategory": "หมวดหมู่ครุภัณฑ์",
            "quantity": "จำนวน",
            "unit": "หน่วยนับ",
            "purchase_price": "ราคาที่ซื้อ",
            "purchase_date": "วันที่ซื้อ",
            "fiscal_year": "ปีที่ใช้งาน",
            "lifetime": "อายุการใช้งาน (ปี)",
            "used_years": "ใช้มาแล้วกี่ปี",
            "responsible_person": "ผู้รับผิดชอบ",
            "storage_location": "สถานที่เก็บ",
            "brand_model": "ยี่ห้อ/รุ่น",
            "damage_status": "สถานะการใช้งาน",
            "notes": "หมายเหตุ",
            "asset_image": "รูปภาพครุภัณฑ์",
            "status_borrowing": "ครุภัณฑ์ที่ยืมได้", # ✅ เพิ่ม label ให้ฟิลด์ใหม่
            "status_assetloan": "สถานะการยืม", # ✅ เพิ่ม label ให้ฟิลด์ใหม่
        }
        widgets = {
            "notes": forms.Textarea(attrs={
                "rows": 2,
                "cols": 40,
                "class": "form-control"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ✅ ลบ '---------' ออกจาก category
        self.fields['subcategory'].empty_label = None



# class AssetItemForm(forms.ModelForm):
#     # เพิ่มฟอร์มสำหรับสร้างรหัสครุภัณฑ์
#     asset_code = forms.ModelChoiceField(
#         queryset=AssetCode.objects.all(),
#         required=False,
#         label="รหัสครุภัณฑ์ (เลือกหรือสร้างใหม่)"
#     )

#     class Meta:
#         model = AssetItem
#         fields = [
#             "item_name", "category", "asset_code", "quantity", "unit", 
#             "purchase_price", "purchase_date", "fiscal_year", "lifetime", "used_years", 
#             "responsible_person", "storage_location", "brand_model", "damage_status", 
#             "notes", "asset_image"
#         ]
#         labels = {
#             "item_name": "ชื่อรายการครุภัณฑ์",
#             "category": "หมวดหมู่ครุภัณฑ์",
#             "quantity": "จำนวน",
#             "unit": "หน่วยนับ",
#             "purchase_price": "ราคาที่ซื้อ",
#             "purchase_date": "วันที่ซื้อ",
#             "fiscal_year": "ปีที่ใช้งาน",
#             "lifetime": "อายุการใช้งาน (ปี)",
#             "used_years": "ใช้มาแล้วกี่ปี",
#             "responsible_person": "ผู้รับผิดชอบ",
#             "storage_location": "สถานที่เก็บ",
#             "brand_model": "ยี่ห้อ/รุ่น",
#             "damage_status": "สถานะการใช้งาน",
#             "notes": "หมายเหตุ",
#             "asset_image": "รูปภาพครุภัณฑ์",
#         }
#         widgets = {
#             "notes": forms.Textarea(attrs={
#                 "rows": 2,   # ปรับให้สั้นลง
#                 "cols": 40,  # ปรับความกว้าง
#                 "class": "form-control"
#             }),
#         }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = AssetCategory
        fields = ['name_cate']

class SubcategoryForm(forms.ModelForm):
    class Meta:
        model = Subcategory
        fields = ['name_sub', 'category']

class StorageLocationForm(forms.ModelForm):
    class Meta:
        model = StorageLocation
        fields = ['name']



# # ฟอร์มบันทึกรายการครุภัณฑ์
# class AssetItemForm(forms.ModelForm):
#     class Meta:
#         model = AssetItem
#         fields = '__all__'
#         widgets = {
#             'purchase_date': forms.DateInput(attrs={'type': 'date'}),
#             'start_date': forms.DateInput(attrs={'type': 'date'}),
#         }

# ฟอร์มบันทึกการครอบครอบครุภัณฑ์
class AssetOwnershipForm(forms.ModelForm):
    class Meta:
        model = AssetOwnership
        fields = '__all__'
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

# ฟอร์มตรวจเช็ครายการครุภัณฑ์
class AssetCheckForm(forms.ModelForm):
    # ฟิลด์สถานะการตรวจเช็ค (ติ๊กว่าได้ตรวจแล้ว)
    status = forms.BooleanField(
        required=False,
        label="ตรวจแล้ว"
    )

    # ฟิลด์สถานะการใช้งาน (ให้เลือกจากตัวเลือกที่มี)
    damage_status = forms.ChoiceField(
        choices=AssetItem.DAMAGE_STATUS_CHOICES,
        required=False,
        label="สถานะการใช้งาน"
    )

    # ฟิลด์ผู้รับผิดชอบดูแลกำกับ (สามารถเปลี่ยนแปลงได้)
    responsible_person = forms.CharField(
        required=False,
        label="ผู้รับผิดชอบดูแลกำกับ"
    )

    # **ฟิลด์สถานที่เก็บ** (สามารถเปลี่ยนแปลงได้)
    storage_location = forms.ModelChoiceField(
        queryset=StorageLocation.objects.all(),
        required=False,
        label="สถานที่เก็บ"
    )

    class Meta:
        model = AssetCheck
        fields = ["status", "damage_status", "responsible_person", "storage_location"]

    def __init__(self, *args, **kwargs):
        self.asset = kwargs.pop('asset', None)  # รับค่าครุภัณฑ์ที่ต้องการตรวจเช็ค
        super().__init__(*args, **kwargs)

        if self.asset:
            # กำหนดค่าเริ่มต้นให้ตรงกับข้อมูลของครุภัณฑ์นั้น
            self.fields['damage_status'].initial = self.asset.damage_status
            self.fields['responsible_person'].initial = self.asset.responsible_person
            self.fields['storage_location'].initial = self.asset.storage_location  # กำหนดค่าเริ่มต้นให้ตรงกับสถานที่เก็บปัจจุบันของครุภัณฑ์

    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        if user:
            instance.user = user  # ตั้งค่าผู้ตรวจเช็คเป็นผู้ใช้ที่ล็อกอินอยู่
        if self.asset:
            # อัปเดตค่าใน AssetItem ด้วยค่าที่ผู้ใช้กรอก
            self.asset.damage_status = self.cleaned_data['damage_status']
            self.asset.responsible_person = self.cleaned_data['responsible_person']
            self.asset.storage_location = self.cleaned_data['storage_location']  # **อัปเดตสถานที่เก็บ**
            self.asset.save()  # บันทึกค่าที่เปลี่ยนแปลงของครุภัณฑ์
        if commit:
            instance.save()
        return instance
    

# การขอยืมครุภัณฑ์
class AssetLoanForm(forms.ModelForm):
    class Meta:
        model = AssetLoan
        fields = ["asset", "date_due", "remarks"]
        widgets = {
            "date_due": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

# อนุมัติหรือปฏิเสธคำขอยืมครุภัณฑ์ 
class AssetLoanApprovalForm(forms.ModelForm):
    class Meta:
        model = AssetLoan
        fields = ["status"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
        }

# ยืนยันรับครุภัณฑ์
class AssetLoanConfirmForm(forms.ModelForm):
    class Meta:
        model = AssetLoan
        fields = ['confirm']
        widgets = {
            'confirm': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

#  แจ้งคืนครุภัณฑ์
class AssetReturnForm(forms.ModelForm):
    class Meta:
        model = AssetLoan
        fields = ["remarks"]  # ให้ผู้ยืมสามารถเพิ่มหมายเหตุเกี่ยวกับการคืนได้
        widgets = {
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }       

# อนุมัติการคืน
class ApproveReturnForm(forms.ModelForm):
    class Meta:
        model = AssetLoan
        fields = ["status"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
        }
