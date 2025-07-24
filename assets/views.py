from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import AssetCode, AssetItem, AssetCheck, AssetLoan, StorageLocation
from .forms import AssetCheckForm, AssetCodeForm, AssetItemForm, AssetLoanApprovalForm, AssetLoanForm, AssetOwnershipForm
from django.utils import timezone
from django.contrib import messages


# Create your views here.
# def base(request):
# 	return render(request, 'base_sidebar.html')

def home_assets(request):
    return render(request, 'home_assets.html')


def asset_list(request):
    return render(request, 'asset_list.html')


def repair_report(request):
    return render(request, 'repair_report.html')


# # บันทึกรายการครุภัณฑ์
# @login_required
# def create_asset_item(request):
#     if request.method == 'POST':
#         form = AssetItemForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect('assets:asset_list')  # เปลี่ยนไปหน้ารายการครุภัณฑ์หลังจากบันทึก
#     else:
#         form = AssetItemForm()
#     return render(request, 'create_asset_item.html', {'form': form})


# บันทึกรายการครุภัณฑ์
def add_asset_item(request):
    if request.method == "POST":
        asset_code_form = AssetCodeForm(request.POST)
        asset_item_form = AssetItemForm(request.POST, request.FILES)

        if asset_code_form.is_valid() and asset_item_form.is_valid():
            # เช็คว่ามีรหัสครุภัณฑ์อยู่แล้วหรือไม่
            asset_code, created = AssetCode.objects.get_or_create(
                asset_type=asset_code_form.cleaned_data["asset_type"],
                asset_kind=asset_code_form.cleaned_data["asset_kind"],
                asset_character=asset_code_form.cleaned_data["asset_character"],
                serial_year=asset_code_form.cleaned_data["serial_year"],
            )

            # บันทึกรายการครุภัณฑ์
            asset_item = asset_item_form.save(commit=False)
            asset_item.asset_code = asset_code
            asset_item.save()

            return redirect("asset:asset_list")  # เปลี่ยนเส้นทางไปหน้ารายการครุภัณฑ์

    else:
        asset_code_form = AssetCodeForm()
        asset_item_form = AssetItemForm()

    return render(request, "add_asset_item.html", {
        "asset_code_form": asset_code_form,
        "asset_item_form": asset_item_form
    })


# บันทึกการครอบครองครุภัณฑ์
@login_required
def create_asset_ownership(request):
    if request.method == 'POST':
        form = AssetOwnershipForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('assets:ownership_list')  # เปลี่ยนไปหน้ารายการการครอบครองครุภัณฑ์
    else:
        form = AssetOwnershipForm()
    return render(request, 'create_asset_ownership.html', {'form': form})


# บันทึกการตรวจเช็คครุภัณฑ์
@login_required
def check_asset(request, asset_id):
    # ดึงข้อมูลครุภัณฑ์ที่ต้องการตรวจเช็ค
    asset = get_object_or_404(AssetItem, id=asset_id)
    storage_locations = StorageLocation.objects.all()  # ดึงสถานที่เก็บทั้งหมด

    if request.method == "POST":
        form = AssetCheckForm(request.POST, asset=asset)
        if form.is_valid():
            form.save(user=request.user)
            # อัปเดตสถานที่เก็บ
            asset.storage_location_id = request.POST.get("storage_location")
            asset.save()
            return redirect('asset:asset_list')  # เปลี่ยนไปหน้ารายการครุภัณฑ์หลังบันทึก
    else:
        form = AssetCheckForm(asset=asset)

    return render(request, "asset_check_form.html", {"form": form, "asset": asset, "storage_locations": storage_locations})

# รายการยืม
def loan_list(request):
    """แสดงรายการยืมของผู้ใช้"""
    loans = AssetLoan.objects.filter(user=request.user).order_by("-loan_date")
    return render(request, "loan_list.html", {"loans": loans})


def request_loan(request):
    """ส่งคำขอยืม"""
    if request.method == "POST":
        form = AssetLoanForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.user = request.user
            loan.status = "pending"  # ตั้งค่าเป็นรออนุมัติ
            loan.save()
            messages.success(request, "ส่งคำขอยืมสำเร็จ รอการอนุมัติ")
            return redirect("asset:loan_list")
    else:
        form = AssetLoanForm()

    return render(request, "request_loan.html", {"form": form})


def loan_approval(request, loan_id):
    """อนุมัติหรือปฏิเสธคำขอ"""
    loan = get_object_or_404(AssetLoan, id=loan_id)
    asset = loan.asset  # ดึงครุภัณฑ์ที่ถูกยืมมาใช้งาน

    if request.method == "POST":
        form = AssetLoanApprovalForm(request.POST, instance=loan)
        if form.is_valid():
            loan = form.save(commit=False)

            if loan.status == "approved":
                loan.status = "borrowed"  # เปลี่ยนเป็น "กำลังยืม"
                asset.status_assetloan = True  # เปลี่ยนสถานะครุภัณฑ์เป็นถูกยืม
                messages.success(request, f"อนุมัติการยืมของ {loan.user.username}")
            
            elif loan.status == "rejected":
                asset.status_assetloan = False  # กรณีปฏิเสธ ให้คืนสถานะว่าว่าง
                messages.warning(request, f"ปฏิเสธคำขอของ {loan.user.username}")

            loan.save()
            asset.save()  # บันทึกสถานะครุภัณฑ์
            return redirect("asset:loan_approval_list")
    else:
        form = AssetLoanApprovalForm(instance=loan)

    return render(request, "loan_approval.html", {"form": form, "loan": loan})


def confirm_receipt(request, loan_id):
    """ยืนยันการรับครุภัณฑ์"""
    loan = get_object_or_404(AssetLoan, id=loan_id, user=request.user)
    
    if loan.status == "approved" and not loan.confirm:
        loan.confirm = True
        loan.status = "borrowed"  # เปลี่ยนเป็นสถานะ "กำลังยืม"
        loan.date_received = timezone.now()
        loan.save()
        messages.success(request, "ยืนยันรับครุภัณฑ์เรียบร้อยแล้ว")
    else:
        messages.warning(request, "ไม่สามารถยืนยันรับครุภัณฑ์ได้")
    
    return redirect("asset:loan_list")


def request_return(request, loan_id):
    """แจ้งคืนครุภัณฑ์"""
    loan = get_object_or_404(AssetLoan, id=loan_id, user=request.user)

    if loan.status == "borrowed":
        loan.status = "returned_pending"  # แจ้งคืน
        loan.save()
        messages.success(request, "แจ้งคืนครุภัณฑ์แล้ว รอการอนุมัติ")
    
    return redirect("asset:loan_list")


def approve_return(request, loan_id):
    """อนุมัติการคืน"""
    loan = get_object_or_404(AssetLoan, id=loan_id)

    if loan.status == "returned_pending":
        loan.date_of_return = timezone.now().date()
        loan.status = "returned"
        loan.save()

        # อัปเดตสถานะการยืมของครุภัณฑ์
        loan.asset.status_assetloan = False
        loan.asset.save()

        messages.success(request, f"อนุมัติการคืนของ {loan.user.username}")
    
    return redirect("asset:loan_approval_list")
