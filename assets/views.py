
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from assets.helpers import get_clean_cart
from assets.models import AssetCode, AssetItem, AssetCheck, StorageLocation, AssetCategory, Subcategory, StorageLocation,OrderAssetLoan,IssuingAssetLoan
from .forms import ApproveLoanForm, AssetCheckForm, AssetCodeForm, AssetItemForm, CategoryForm, LoanForm, SubcategoryForm, StorageLocationForm,StorageLocationForm
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
import qrcode
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from io import BytesIO
from datetime import date
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
from django.http import JsonResponse
import json # นำเข้าโมดูล json



def home_assets(request):
    return render(request, 'home_assets.html')


# รายการครุภัณฑ์
def asset_list(request):
    # ดึงข้อมูลรายการครุภัณฑ์ทั้งหมด
    assets_list = AssetItem.objects.all().order_by('id')

    # สร้าง Paginator object
    paginator = Paginator(assets_list, 10) # แสดง 10 รายการต่อหน้า

    page = request.GET.get('page')
    try:
        assets = paginator.page(page)
    except PageNotAnInteger:
        # ถ้าไม่มีหมายเลขหน้า ให้แสดงหน้าแรก
        assets = paginator.page(1)
    except EmptyPage:
        # ถ้าหมายเลขหน้าเกินจำนวนหน้าทั้งหมด ให้แสดงหน้าสุดท้าย
        assets = paginator.page(paginator.num_pages)
    
    # ส่งข้อมูล assets ที่ถูกแบ่งหน้าแล้วไปยัง template
    return render(request, 'asset_list.html', {'assets': assets})


def add_asset_item(request):
    categories = AssetCategory.objects.prefetch_related("subcategories").all()

    if request.method == "POST":
        asset_code_form = AssetCodeForm(request.POST)
        asset_item_form = AssetItemForm(request.POST, request.FILES)

        if asset_code_form.is_valid() and asset_item_form.is_valid():
            try:
                # บันทึก AssetCode ก่อนเพื่อตรวจสอบว่า serial_year ซ้ำหรือไม่
                asset_code = asset_code_form.save()
                
                # ผูก asset_code เข้ากับรายการ
                asset_item = asset_item_form.save(commit=False)
                asset_item.asset_code = asset_code
                
                # ใช้ฟังก์ชัน save() ของ AssetItem ที่เราแก้ไขไว้
                asset_item.save()

                messages.success(request, "✅ บันทึกรายการครุภัณฑ์เรียบร้อยแล้ว")
                return redirect("assets:asset_list")

            except IntegrityError:
                # จัดการกรณีที่ serial_year ซ้ำ
                messages.error(request, "❌ เกิดข้อผิดพลาด: รหัสลำดับ/ปีนี้มีอยู่ในระบบแล้ว")
            except Exception as e:
                messages.error(request, f"❌ เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")
        else:
            messages.error(request, "❌ กรุณาตรวจสอบความถูกต้องของข้อมูลในฟอร์ม")
    else:
        asset_code_form = AssetCodeForm()
        asset_item_form = AssetItemForm()

    return render(request, "add_asset_item.html", {
        "asset_code_form": asset_code_form,
        "asset_item_form": asset_item_form,
        "categories": categories,
    })


# รายละเอียดครุภัณฑ์
def asset_detail(request, pk):
    """ฟังก์ชันสำหรับแสดงรายละเอียดของครุภัณฑ์"""
    asset = get_object_or_404(AssetItem, pk=pk)
    # หากต้องการใช้ฟังก์ชัน calculate_annual_depreciation
    annual_depreciation = asset.calculate_annual_depreciation()
    return render(request, 'asset_detail.html', {
        'asset': asset,
        'annual_depreciation': annual_depreciation
    })


# แก้ไขครุภัณฑ์
def asset_edit(request, pk):
    """ฟังก์ชันสำหรับแก้ไขข้อมูลครุภัณฑ์"""
    asset = get_object_or_404(AssetItem, pk=pk)
    
    if request.method == 'POST':
        asset_item_form = AssetItemForm(request.POST, request.FILES, instance=asset)
        asset_code_form = AssetCodeForm(request.POST, instance=asset.asset_code)
        
        if asset_item_form.is_valid() and asset_code_form.is_valid():
            try:
                # บันทึก asset_code ก่อนเพื่อตรวจสอบความถูกต้องและป้องกัน IntegrityError
                asset_code_form.save()
                
                # บันทึก asset_item โดยไม่ต้อง commit ก่อน
                asset_item = asset_item_form.save(commit=False)
                
                # ใช้เมธอด save() ของโมเดล AssetItem ที่เราได้ปรับปรุงไว้
                # ซึ่งจะจัดการการคำนวณค่าเสื่อมและสร้าง QR code โดยอัตโนมัติ
                asset_item.save()

                messages.success(request, '✅ แก้ไขข้อมูลครุภัณฑ์เรียบร้อยแล้ว')
                return redirect('assets:asset_detail', pk=asset.pk)
            
            except IntegrityError:
                # จัดการกรณีที่ serial_year ซ้ำ
                messages.error(request, '❌ รหัสครุภัณฑ์ (ลำดับ/ปี) นี้มีอยู่ในระบบแล้ว กรุณาตรวจสอบ')
            except Exception as e:
                messages.error(request, f'❌ เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}')
        else:
            messages.error(request, '❌ กรุณาตรวจสอบความถูกต้องของข้อมูลในฟอร์ม')
    else:
        # สร้างฟอร์มสำหรับแสดงผลในหน้า edit
        asset_item_form = AssetItemForm(instance=asset)
        asset_code_form = AssetCodeForm(instance=asset.asset_code)
    
    categories = AssetCategory.objects.prefetch_related("subcategories").all()
    
    return render(request, 'asset_edit.html', {
        'asset_item_form': asset_item_form,
        'asset_code_form': asset_code_form,
        'asset': asset,
        'categories': categories,
    })

# ลบครุภัณฑ์
def asset_delete(request, pk):
    """
    ฟังก์ชันสำหรับลบข้อมูลครุภัณฑ์
    จะทำงานเฉพาะเมื่อได้รับ POST request จาก Modal ในหน้า asset_list เท่านั้น
    """
    if request.method == 'POST':
        asset = get_object_or_404(AssetItem, pk=pk)
        asset_code_to_delete = asset.asset_code
        asset.delete()
        
        # ตรวจสอบว่ามีรายการอื่นใช้ AssetCode นี้หรือไม่ ถ้าไม่ใช้ให้ลบทิ้ง
        if not AssetItem.objects.filter(asset_code=asset_code_to_delete).exists():
            asset_code_to_delete.delete()
            
        messages.success(request, '🗑️ ลบรายการครุภัณฑ์เรียบร้อยแล้ว')
        return redirect('assets:asset_list')
        
    # หากเข้าถึง URL นี้ด้วย GET request จะถูก redirect กลับไปที่หน้ารายการ
    return redirect('assets:asset_list')

# -------------------------------------------------------------------------------------------------------------------------------------------

# บันทึกการครอบครองครุภัณฑ์
# @login_required
# def create_asset_ownership(request):
#     if request.method == 'POST':
#         form = AssetOwnershipForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('assets:ownership_list')  # เปลี่ยนไปหน้ารายการการครอบครองครุภัณฑ์
#     else:
#         form = AssetOwnershipForm()
#     return render(request, 'create_asset_ownership.html', {'form': form})


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

# ------------------------------------------------------------------------------------------------------------------------------------

# ------------------------------
# แสดงรายการครุภัณฑ์
# ------------------------------
@login_required
def loan_list(request):
    query = request.GET.get("q", "")
    category_id = request.GET.get("category")
    subcategory_id = request.GET.get("subcategory")

    asset_items = AssetItem.objects.filter(status_borrowing=True)

    if query:
        asset_items = asset_items.filter(
            Q(item_name__icontains=query) |
            Q(asset_code__asset_type__icontains=query) |
            Q(asset_code__asset_kind__icontains=query)
        )

    selected_category = None
    if category_id:
        selected_category = get_object_or_404(AssetCategory, id=category_id)
        asset_items = asset_items.filter(subcategory__category=selected_category)

    selected_subcategory = None
    if subcategory_id:
        selected_subcategory = get_object_or_404(Subcategory, id=subcategory_id)
        asset_items = asset_items.filter(subcategory=selected_subcategory)

    context = {
        "asset_items": asset_items,
        "categories": AssetCategory.objects.all(),
        "subcategories": Subcategory.objects.all(),
        "selected_category": selected_category,
        "selected_subcategory": selected_subcategory,
        "query": query,
    }
    return render(request, "loan_list.html", context)


# ------------------------------
# แสดงตะกร้า
# ------------------------------
@login_required
def loan_cart(request):
    asset_items = AssetItem.objects.filter(status_borrowing=True)

    context = {
        "asset_items": asset_items
    }
    return render(request, "loan_cart.html", context)


# ------------------------------
# แสดงรายละเอียดครุภัณฑ์
# ------------------------------
# @login_required
# def loan_detail(request, asset_id):
#     asset = get_object_or_404(AssetItem, id=asset_id)

#     context = {
#         "asset": asset,
#     }
#     return render(request, "loan_detail.html", context)

def loan_detail_view(request, loan_id):
    loan = get_object_or_404(OrderAssetLoan, pk=loan_id)
    context = {
        'loan': loan,
    }
    return render(request, 'loan_detail.html', context)

# ------------------------------
# ยืนยันการยืม
# ------------------------------
@login_required
def confirm_loan(request):
    if request.method == "POST":
        asset_ids_str = request.POST.get("asset_ids", "")
        asset_ids = [int(i) for i in asset_ids_str.split(",") if i.isdigit()]
        assets_in_cart = AssetItem.objects.filter(id__in=asset_ids)

        if not assets_in_cart:
            messages.error(request, "ไม่มีครุภัณฑ์ในตะกร้า")
            return redirect("assets:loan_list")

        form = LoanForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.status = "pending"
            order.save()

            for asset in assets_in_cart:
                IssuingAssetLoan.objects.create(order_asset=order, asset=asset)
                asset.status_assetloan = True
                asset.save()

            messages.success(request, "ส่งคำขอยืมครุภัณฑ์เรียบร้อย")
            return redirect("assets:loan_list")

    return redirect("assets:loan_list")



@login_required
def loan_approval_list(request):
    """
    หน้าแสดงรายการคำขออนุมัติการยืมและคืนครุภัณฑ์
    """
    # กรองคำขอที่รออนุมัติและรออนุมัติการคืน
    qs = OrderAssetLoan.objects.all()
    
    # pagination (ไม่บังคับ แต่ช่วยให้หน้าไม่ยาวเกินไป)
    paginator = Paginator(qs, 15)  # แสดง 15 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'loan_approval_list.html', context)



def loan_approval(request, pk):
    loan = get_object_or_404(OrderAssetLoan, pk=pk)

    if request.method == "POST":
        action = request.POST.get("status")

        if action == "approved" and loan.status == "pending":
            loan.status = "approved"
            loan.date_approved = timezone.now()
            loan.save()
            messages.success(request, "อนุมัติการยืมเรียบร้อยแล้ว ✅")

        elif action == "rejected" and loan.status == "pending":
            loan.status = "rejected"
            loan.date_updated = timezone.now()
            loan.save()
            messages.error(request, "ปฏิเสธการยืมเรียบร้อยแล้ว ❌")

        else:
            messages.warning(request, "ไม่สามารถทำรายการนี้ได้")

    return redirect("assets:loan_approval_list")
    


def approve_return(request, loan_id):
    loan = get_object_or_404(OrderAssetLoan, loan_id=loan_id)

    if loan.status == "returned_pending":
        loan.status = "returned"
        loan.date_received = timezone.now().date()
        loan.received_by = request.user.username
        loan.confirm_received = True
        loan.save()

        # คืนสถานะครุภัณฑ์ทุกชิ้น
        for issuing in loan.items.all():
            asset = issuing.asset
            asset.status_assetloan = False  # คืนแล้ว
            asset.save()

        messages.success(request, "อนุมัติการคืนเรียบร้อยแล้ว")
    else:
        messages.warning(request, "ไม่สามารถอนุมัติการคืนได้")

    return redirect("assets:loan_approval_list")


# @login_required
# def approve_return(request, loan_id):
#     """ผู้ดูแล อนุมัติการคืน"""
#     loan = get_object_or_404(OrderAssetLoan, id=loan_id)
#     asset = loan.asset

#     if loan.status == "returned_pending":
#         loan.date_of_return = timezone.now().date()
#         loan.status = "returned"
#         loan.save()

#         asset.status_assetloan = False  # คืนของแล้ว ใช้งานได้อีก
#         asset.save()

#         messages.success(request, f"อนุมัติการคืนของ {loan.user.username}")
#     else:
#         messages.warning(request, "ไม่สามารถอนุมัติการคืนได้")

#     return redirect("assets:loan-approval-list")



# --------------------------------------------------------------------------------------------

# รายการหมวดหมู่
def asset_list_cate(request):
    query = request.GET.get('q')  # รับค่าค้นหาจาก input ชื่อ 'q'

    # เรียกข้อมูลทั้งหมดหรือกรองตามการค้นหา
    if query:
        categories = AssetCategory.objects.filter(
            Q(name_cate__icontains=query)
        )
    else:
        categories = AssetCategory.objects.all()

    # ✅ เช็คถ้ามีการส่ง POST เพื่อเพิ่มหมวดหมู่
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ เพิ่มหมวดหมู่หลักเรียบร้อยแล้ว')
            return redirect('assets:asset_list_cate')
        else:
            messages.error(request, '❌ ไม่สามารถเพิ่มหมวดหมู่หลักได้ กรุณาตรวจสอบข้อมูล')
    else:
        form = CategoryForm()


    page = request.GET.get('page')

    p = Paginator(categories, 5)
    try:
        categories = p.page(page)
    except:
        categories = p.page(1)

    return render(request, 'asset_list_cate.html', {
        'categories': categories,
        'form': form,
        'query': query,  # ส่งค่าการค้นหาไปยัง template เพื่อแสดงผล
    })

# เพิ่มหมวดหมู่
def add_category_asset(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ เพิ่มหมวดหมู่หลักเรียบร้อยแล้ว')
            return redirect('assets:add_category_asset')
        else:
            messages.error(request, '❌ ไม่สามารถเพิ่มหมวดหมู่หลักได้ กรุณาตรวจสอบข้อมูล')
    else:
        form = CategoryForm()
    return render(request, 'add_category_asset.html', {'form': form})

# แก้ไขหมวดหมู่
def edit_category_asset(request, pk):
    category = get_object_or_404(AssetCategory, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ แก้ไขหมวดหมู่หลักเรียบร้อยแล้ว')
            return redirect('assets:asset_list_cate')
        else:
            messages.error(request, '❌ แก้ไขไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'asset_list_cate.html', {'form': form})

# ลบหมวดหมู่หลัก
def delete_category_asset(request, pk):
    category = get_object_or_404(AssetCategory, pk=pk)
    category.delete()
    messages.success(request, '🗑 ลบหมวดหมู่หลักเรียบร้อยแล้ว')
    return redirect('assets:asset_list_cate')

# --------------------------------------------------------------------------------------------


# รายการหมวดหมู่ย่อย
def asset_list_subcate(request):
    query = request.GET.get('q')

    # ✅ แก้ไขตรงนี้: กำหนดค่า subcategories_list ไว้ก่อน
    if query:
        # ถ้ามีคำค้นหา ให้กรองข้อมูล
        subcategories_list = Subcategory.objects.filter(
            Q(name_sub__icontains=query) |
            Q(category__name_cate__icontains=query)
        ).order_by('id')
    else:
        # ถ้าไม่มีคำค้นหา ให้ดึงข้อมูลทั้งหมด
        subcategories_list = Subcategory.objects.all().order_by('id')

    # ดึงรายการหมวดหมู่หลักทั้งหมดสำหรับ Modal (แยกจาก Paginator)
    categories = AssetCategory.objects.all()

    if request.method == 'POST':
        form = SubcategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ เพิ่มหมวดหมู่ย่อยเรียบร้อยแล้ว')
            return redirect('assets:asset_list_subcate')
        else:
            messages.error(request, '❌ ไม่สามารถเพิ่มหมวดหมู่ย่อยได้ กรุณาตรวจสอบข้อมูล')
    else:
        form = SubcategoryForm()

    page = request.GET.get('page')

    # ✅ Paginator จะสร้างจาก subcategories_list ที่ถูกกำหนดค่าแล้วเสมอ
    p = Paginator(subcategories_list, 10)
    try:
        subcategories = p.page(page)
    except PageNotAnInteger:
        subcategories = p.page(1)
    except EmptyPage:
        subcategories = p.page(p.num_pages)

    return render(request, 'asset_list_subcate.html', {
        'subcategories': subcategories,
        'categories': categories,
        'form': form,
        'query': query,
    })

# เพิ่มหมวดหมู่ย่อย
def add_subcategory_asset(request):
    if request.method == 'POST':
        form = SubcategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ เพิ่มหมวดหมู่ย่อยเรียบร้อยแล้ว')
            return redirect('assets:add_subcategory_asset')
        else:
            messages.error(request, '❌ ไม่สามารถเพิ่มหมวดหมู่ย่อยได้ กรุณาตรวจสอบข้อมูล')
    else:
        form = SubcategoryForm()
    return render(request, 'add_subcategory_asset.html', {'form': form})

# แก้ไขหมวดหมู่ย่อย
def edit_subcategory_asset(request, pk):
    category = get_object_or_404(Subcategory, pk=pk)
    if request.method == 'POST':
        form = SubcategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ แก้ไขหมวดหมู่ย่อยเรียบร้อยแล้ว')
            return redirect('assets:asset_list_subcate')
        else:
            messages.error(request, '❌ แก้ไขไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    else:
        form = SubcategoryForm(instance=category)

    return render(request, 'asset_list_subcate.html', {'form': form})

# ลบหมวดหมู่ย่อย
def delete_subcategory_asset(request, pk):
    subcategory = get_object_or_404(Subcategory, pk=pk)
    subcategory.delete()
    messages.success(request, '🗑 ลบหมวดหมู่ย่อยเรียบร้อยแล้ว')
    return redirect('assets:asset_list_subcate')

# --------------------------------------------------------------------------------------------


# def add_storage_location(request):
#     if request.method == 'POST':
#         form = StorageLocationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, '✅ เพิ่มสถานที่เก็บเรียบร้อยแล้ว')
#             return redirect('assets:add_storage_location')
#         else:
#             messages.error(request, '❌ ไม่สามารถเพิ่มสถานที่เก็บได้ กรุณาตรวจสอบข้อมูล')
#     else:
#         form = StorageLocationForm()
#     return render(request, 'add_storage_location.html', {'form': form})


# รายสถานที่เก็บครุภัณฑ์ และเพิ่มรายการ
def asset_list_storage_location(request):
    query = request.GET.get('q')  # รับค่าค้นหาจาก input ชื่อ 'q'

    # เรียกข้อมูลทั้งหมดหรือกรองตามการค้นหา
    if query:
        storagelocations = StorageLocation.objects.filter(
            Q(name__icontains=query)
        )
    else:
        storagelocations = StorageLocation.objects.all()

    if request.method == 'POST':
        form = StorageLocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ เพิ่มสถานที่เก็บครุภัณฑ์เรียบร้อยแล้ว')
            return redirect('assets:asset_list_storage_location')
        else:
            messages.error(request, '❌ ไม่สามารถเพิ่มสถานที่เก็บครุภัณฑ์ได้ กรุณาตรวจสอบข้อมูล')
    else:
        form = StorageLocationForm()

    return render(request, 'asset_list_location.html', {
        'storagelocations': storagelocations,
        'form': form,
        'query': query,  # ส่งค่าการค้นหาไปยัง template เพื่อแสดงผล
    })


# ✅ แก้ไขรายการสถานที่เก็บครุภัณฑ์
def edit_storage_location_asset(request, pk):
    storagelocation = get_object_or_404(StorageLocation, pk=pk)  # ✅ Model ชื่อ StorageLocation

    if request.method == 'POST':
        form = StorageLocationForm(request.POST, instance=storagelocation)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ แก้ไขสถานที่เก็บครุภัณฑ์เรียบร้อยแล้ว')
            return redirect('assets:asset_list_storage_location')
        else:
            messages.error(request, '❌ แก้ไขไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    else:
        form = StorageLocationForm(instance=storagelocation)

    return render(request, 'asset_list_location.html', {'form': form})


# ✅ ลบรายการสถานที่เก็บครุภัณฑ์
def delete_storage_location_asset(request, pk):
    storagelocation = get_object_or_404(StorageLocation, pk=pk)  # ✅ Model ชื่อ StorageLocation
    storagelocation.delete()
    messages.success(request, '🗑 ลบรายการสถานที่เก็บครุภัณฑ์เรียบร้อยแล้ว')
    return redirect('assets:asset_list_storage_location')  # เปลี่ยนชื่อให้ตรงกับ url ที่ใช้งาน
