from django import forms
from .models import AssetCheck, AssetCode, AssetItem, AssetItemLoan, AssetOwnership, AssetReservation, StorageLocation, AssetCategory, Subcategory, StorageLocation,OrderAssetLoan


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
            "item_name", "subcategory", "unit", "purchase_price", "purchase_date", 
            "fiscal_year", "lifetime", "used_years", 
            "responsible_person", "storage_location", 
            "brand_model", "damage_status", "notes", "asset_image",
            "status_borrowing", "status_assetloan", # ✅ เพิ่ม 2 ฟิลด์นี้
        ]
        labels = {
            "item_name": "ชื่อรายการครุภัณฑ์",
            "subcategory": "หมวดหมู่ครุภัณฑ์",
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


class AssetItemLoanForm(forms.ModelForm):
    class Meta:
        model = AssetItemLoan
        fields = [
            'item_name', 
            'subcategory', 
            'asset_code', 
            'unit', 
            'storage_location', 
            'brand_model', 
            'notes', 
            'damage_status', 
            'status_assetloan',
            'status_borrowing',
            'asset_image',
        ]
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'subcategory': forms.Select(attrs={'class': 'form-control'}),
            'asset_code': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'storage_location': forms.Select(attrs={'class': 'form-control'}),
            'brand_model': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control'}),
            'damage_status': forms.Select(attrs={'class': 'form-control'}),
            'status_assetloan': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status_borrowing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


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



# ฟอร์มสำหรับการยืมครุภัณฑ์ (Checkout Form)
class LoanForm(forms.ModelForm):
    class Meta:
        model = OrderAssetLoan
        fields = ["date_of_use", "date_due"]
        widgets = {
            "date_of_use": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_due": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
        labels = {
            "date_of_use": "วันที่ใช้งาน",
            "date_due": "วันที่กำหนดคืน",
        }

# ฟอร์มสำหรับการจองครุภัณฑ์ (Checkout Form)
class ReservationForm(forms.ModelForm):
    class Meta:
        model = AssetReservation
        fields = ['reserved_date', 'returning_date', 'notes']
        widgets = {
            'reserved_date': forms.DateInput(attrs={'type': 'date'}),
            'returning_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

# ฟอร์มสำหรับเจ้าหน้าที่อนุมัติ (ชื่อ + ตำแหน่ง + สถานะ)
class ApproveLoanForm(forms.ModelForm):
    class Meta:
        model = OrderAssetLoan
        fields = ["approved_by", "approver_position", "status", "date_approved"]
        widgets = {
            "approved_by": forms.TextInput(attrs={"class": "form-control", "placeholder": "ชื่อเจ้าหน้าที่อนุมัติ"}),
            "approver_position": forms.TextInput(attrs={"class": "form-control", "placeholder": "ตำแหน่งเจ้าหน้าที่"}),
            "status": forms.Select(attrs={"class": "form-select"}, choices=OrderAssetLoan.STATUS_CHOICES_LOAN),
            "date_approved": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
        labels = {
            "approved_by": "ชื่อเจ้าหน้าที่อนุมัติ",
            "approver_position": "ตำแหน่งเจ้าหน้าที่",
            "status": "สถานะการยืม",
            "date_approved": "วันที่อนุมัติ",
        }


# ฟอร์มสำหรับผู้ยืมส่งคืน (ต้องกรอกชื่อด้วย)
class BorrowerReturnForm(forms.ModelForm):
    class Meta:
        model = OrderAssetLoan
        fields = ["returned_by", "date_of_return"]
        widgets = {
            "returned_by": forms.TextInput(attrs={"class": "form-control", "placeholder": "ชื่อผู้คืนครุภัณฑ์"}),
            "date_of_return": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
        labels = {
            "returned_by": "ชื่อผู้คืนครุภัณฑ์",
            "date_of_return": "วันที่ส่งคืนจริง",
        }


# ฟอร์มสำหรับเจ้าหน้าที่รับคืน
class StaffConfirmReturnForm(forms.ModelForm):
    confirm_received = forms.BooleanField(
        required=True, label="ยืนยันการรับคืน", widget=forms.CheckboxInput()
    )

    class Meta:
        model = OrderAssetLoan
        fields = ["received_by", "receiver_position", "confirm_received", "receiver_note", "date_received"]
        widgets = {
            "received_by": forms.TextInput(attrs={"class": "form-control", "placeholder": "ชื่อเจ้าหน้าที่รับคืน"}),
            "receiver_position": forms.TextInput(attrs={"class": "form-control", "placeholder": "ตำแหน่งเจ้าหน้าที่"}),
            "receiver_note": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "ความคิดเห็น/หมายเหตุ"}),
            "date_received": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
        labels = {
            "received_by": "ชื่อเจ้าหน้าที่รับคืน",
            "receiver_position": "ตำแหน่งเจ้าหน้าที่",
            "receiver_note": "ความคิดเห็น",
            "date_received": "วันที่รับคืน",
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
    

# # การขอยืมครุภัณฑ์
# class AssetLoanForm(forms.ModelForm):
#     class Meta:
#         model = AssetLoan
#         fields = ["asset", "date_due", "remarks"]
#         widgets = {
#             "date_due": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
#             "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
#         }

# # อนุมัติหรือปฏิเสธคำขอยืมครุภัณฑ์ 
# class AssetLoanApprovalForm(forms.ModelForm):
#     class Meta:
#         model = AssetLoan
#         fields = ["status"]
#         widgets = {
#             "status": forms.Select(attrs={"class": "form-control"}),
#         }

# # ยืนยันรับครุภัณฑ์
# class AssetLoanConfirmForm(forms.ModelForm):
#     class Meta:
#         model = AssetLoan
#         fields = ['confirm']
#         widgets = {
#             'confirm': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }

# #  แจ้งคืนครุภัณฑ์
# class AssetReturnForm(forms.ModelForm):
#     class Meta:
#         model = AssetLoan
#         fields = ["remarks"]  # ให้ผู้ยืมสามารถเพิ่มหมายเหตุเกี่ยวกับการคืนได้
#         widgets = {
#             "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
#         }       

# # อนุมัติการคืน
# class ApproveReturnForm(forms.ModelForm):
#     class Meta:
#         model = AssetLoan
#         fields = ["status"]
#         widgets = {
#             "status": forms.Select(attrs={"class": "form-control"}),
#         }
