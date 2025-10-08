
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import MyUser
from app_linebot.models import UserLine, UserLine_Asset
from app_linebot.views import notify_admin_assetloan, notify_admin_on_auto_loan, notify_admin_on_return, notify_borrower
from assets.models import AssetCode, AssetItem, AssetCheck, AssetItemLoan, AssetReservation, StorageLocation, AssetCategory, Subcategory, StorageLocation,OrderAssetLoan,IssuingAssetLoan
from dashboard.views import thai_month_name
from .forms import ApproveLoanForm, AssetCheckForm, AssetCodeForm, AssetItemForm, AssetItemLoanForm, CategoryForm, LoanForm, ReservationForm, SubcategoryForm, StorageLocationForm,StorageLocationForm
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Prefetch
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
from linebot import LineBotApi
from linebot.models import TextSendMessage
from django.conf import settings


@login_required
def home_assets(request):
    return render(request, 'home_assets.html')

# รายการครุภัณฑ์
@login_required
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

@login_required
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
@login_required
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
@login_required
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
@login_required
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
            return redirect('assets:asset_list')  # เปลี่ยนไปหน้ารายการครุภัณฑ์หลังบันทึก
    else:
        form = AssetCheckForm(asset=asset)

    return render(request, "asset_check_form.html", {"form": form, "asset": asset, "storage_locations": storage_locations})

# ------------------------------------------------------------------------------------------------------------------------------------

# ------------------------------
# หน้าเพิ่มครุภัณฑ์
# ------------------------------
@login_required
def add_asset_item_loan(request):
    """
    ฟังก์ชันสำหรับเพิ่มรายการครุภัณฑ์สำหรับยืม
    """
    categories = AssetCategory.objects.prefetch_related("subcategories").all()

    if request.method == 'POST':
        form = AssetItemLoanForm(request.POST, request.FILES)
        if form.is_valid():
            asset_item = form.save(commit=False)
            asset_item.save()
            # สามารถเพิ่มข้อความแจ้งเตือน (messages) ได้ที่นี่
            return redirect('assets:loan_list')  # เปลี่ยนเป็น URL ที่ต้องการให้ไปเมื่อบันทึกสำเร็จ
    else:
        form = AssetItemLoanForm()
    
    return render(request, 'add_asset_item_loan.html', 
                  {'form': form,
                  "categories": categories,
                  })

# ------------------------------------
# ฟังก์ชันสำหรับแก้ไขรายการครุภัณฑ์สำหรับยืม
# ------------------------------------
@login_required
def edit_asset_item_loan(request, pk):
    
    asset_item = get_object_or_404(AssetItemLoan, pk=pk)
    categories = AssetCategory.objects.prefetch_related("subcategories").all()

    if request.method == 'POST':
        form = AssetItemLoanForm(request.POST, request.FILES, instance=asset_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขรายการครุภัณฑ์สำหรับยืมสำเร็จแล้ว')
            return redirect('assets:loan_list')
    else:
        form = AssetItemLoanForm(instance=asset_item)
    
    context = {
        'form': form,
        'asset_item': asset_item,
        'categories': categories,
    }
    return render(request, 'edit_asset_item_loan.html', context)


def delete_asset_item_loan(request, pk):
    """
    ฟังก์ชันสำหรับลบรายการครุภัณฑ์สำหรับยืม
    """
    if request.method == 'POST':
        asset_item = get_object_or_404(AssetItemLoan, pk=pk)
        asset_item.delete()
        messages.success(request, 'ลบรายการครุภัณฑ์สำหรับยืมสำเร็จแล้ว')
        return redirect('assets:loan_list')
    # หากผู้ใช้พยายามเข้าถึงด้วย method อื่นที่ไม่ใช่ POST (เช่นพิมพ์ URL ตรงๆ)
    messages.error(request, 'การดำเนินการไม่ถูกต้อง')
    return redirect('assets:loan_list')


@login_required
def calendar_view(request):
    """หน้าเทมเพลตปฏิทิน"""
    return render(request, "calendar.html")


# @login_required
# def calendar_events(request):
#     """ส่งข้อมูลการยืม/จองเป็น JSON ให้ FullCalendar"""
#     events = []

#     # 🎨 Mapping สีตามสถานะ
#     status_colors = {
#         "approved": "#28a745",   # เขียว = อนุมัติ
#         "borrowed": "#28a745",   # เขียว = กำลังยืม
#         "pending":  "#FFA500",   # ส้ม = รออนุมัติ
#         "overdue":  "#FF0000",   # ส้ม = รออนุมัติ
#     }

#     # 🟢 การยืมครุภัณฑ์ (เฉพาะสถานะ approved, borrowed, pending)
#     loans = (
#         OrderAssetLoan.objects
#         .filter(status__in=status_colors.keys())
#         .select_related("user")
#     )

#     for loan in loans:
#         issued_assets = loan.items.all()
#         asset_images_urls = []
#         asset_names = []
#         for issued_asset in issued_assets:
#             if issued_asset.asset and issued_asset.asset.asset_image:
#                 asset_images_urls.append(request.build_absolute_uri(issued_asset.asset.asset_image.url))
#             if issued_asset.asset:
#                 asset_names.append(issued_asset.asset.item_name)
        
#         start_time_loan = timezone.localtime(loan.date_created) if loan.date_created else None
#         end_time_loan = timezone.localtime(loan.date_due) if loan.date_due else None

#         events.append({
#             "title": f"{loan.user.get_first_name()} ยืม : ({', '.join(asset_names)}) {loan.get_status_display()}",
#             "start": start_time_loan.isoformat() if start_time_loan else None,
#             "end": end_time_loan.isoformat() if end_time_loan else None,
#             "color": status_colors.get(loan.status, "#6c757d"),
#             "extendedProps": {
#                 "status": loan.get_status_display(),
#                 "status_color": status_colors.get(loan.status, "#6c757d"), # เพิ่มค่าสีใน extendedProps
#                 "user": loan.user.get_full_name(),
#                 "note": loan.note or "",
#                 "total_assets": loan.get_total_assets, # เก็บจำนวนรายการ
#                 "asset_names": ", ".join(asset_names),
#                 "asset_images": asset_images_urls,
#             }
#         })

#     # 🟡 การจองครุภัณฑ์
#     reservations = (
#         AssetReservation.objects
#         .select_related("user", "asset")
#     )

#     for r in reservations:
#         asset_image_url = None
#         if r.asset and r.asset.asset_image:
#             asset_image_url = request.build_absolute_uri(r.asset.asset_image.url)

#         start_time_res = timezone.localtime(r.reserved_date) if r.reserved_date else None
#         end_time_res = timezone.localtime(r.returning_date) if r.returning_date else None

#         events.append({
#             "title": f"{r.user.get_first_name()} จอง : ({r.asset.item_name})",
#             "start": start_time_res.isoformat() if start_time_res else None,
#             "end": end_time_res.isoformat() if end_time_res else None,
#             "color": "#FFD700",
#             "extendedProps": {
#                 "status": "จองแล้ว",
#                 "status_color": "#FFD700", # เพิ่มค่าสีสำหรับสถานะจอง
#                 "user": r.user.get_full_name(),
#                 "asset": r.asset.item_name,
#                 "notes": r.notes or "",
#                 "asset_image": asset_image_url,
#             }
#         })

#     return JsonResponse(events, safe=False)

@login_required
def calendar_events(request):
    """ส่งข้อมูลการยืม/จองเป็น JSON ให้ FullCalendar"""
    events = []

    # 🎨 Mapping สีตามสถานะ
    status_colors = {
        "approved": "#28a745",   # เขียว = อนุมัติ
        "borrowed": "#28a745",   # เขียว = กำลังยืม
        "pending":  "#FF6600",   # ส้ม = รออนุมัติ
        "overdue":  "#FF0000",   # แดง = เกินกำหนด
    }

    # 🟢 การยืมครุภัณฑ์
    # ให้แน่ใจว่า OrderAssetLoan.objects และ AssetReservation.objects มีอยู่จริงใน scope นี้
    loans = (
        OrderAssetLoan.objects
        .filter(status__in=status_colors.keys())
        .select_related("user")
    )

    for loan in loans:
        issued_assets = loan.items.all()
        asset_images_urls = []
        asset_names = []
        for issued_asset in issued_assets:
            if issued_asset.asset and issued_asset.asset.asset_image:
                # ใช้ request.build_absolute_uri เพื่อสร้าง URL แบบเต็ม
                asset_images_urls.append(request.build_absolute_uri(issued_asset.asset.asset_image.url))
            if issued_asset.asset:
                asset_names.append(issued_asset.asset.item_name)
        
        # *** การแก้ไข Timezone: ใช้เวลาจากฐานข้อมูลโดยตรง (ซึ่งเป็น Timezone-aware UTC) ***
        start_time_loan = loan.date_of_use 
        end_time_loan = loan.date_due 
        
        # ตรวจสอบว่ามีการดึงข้อมูลวัน/เวลามาหรือไม่ ก่อนเรียก .isoformat()
        start_iso = start_time_loan.isoformat() if start_time_loan else None
        end_iso = end_time_loan.isoformat() if end_time_loan else None

        events.append({
            "title": f"{loan.user.get_first_name()} ยืม : ({', '.join(asset_names)}) {loan.get_status_display()}",
            "start": start_iso,
            "end": end_iso,
            "color": status_colors.get(loan.status, "#6c757d"),
            "extendedProps": {
                "status": loan.get_status_display(),
                "status_color": status_colors.get(loan.status, "#6c757d"),
                "user": loan.user.get_full_name(),
                "note": loan.note or "",
                "total_assets": loan.get_total_assets,
                "asset_names": ", ".join(asset_names),
                "asset_images": asset_images_urls,
            }
        })

    # 🟡 การจองครุภัณฑ์
    reservations = (
        AssetReservation.objects
        .select_related("user", "asset")
    )

    for r in reservations:
        asset_image_url = None
        if r.asset and r.asset.asset_image:
            asset_image_url = request.build_absolute_uri(r.asset.asset_image.url)

        # *** การแก้ไข Timezone: ใช้เวลาจากฐานข้อมูลโดยตรง ***
        start_time_res = r.reserved_date 
        end_time_res = r.returning_date 
        
        start_iso = start_time_res.isoformat() if start_time_res else None
        end_iso = end_time_res.isoformat() if end_time_res else None


        events.append({
            "title": f"{r.user.get_first_name()} จอง : ({r.asset.item_name})",
            "start": start_iso,
            "end": end_iso,
            "color": "#FFD700",
            "extendedProps": {
                "status": "จองแล้ว",
                "status_color": "#FFD700", 
                "user": r.user.get_full_name(),
                "asset": r.asset.item_name,
                "notes": r.notes or "",
                "asset_image": asset_image_url,
            }
        })

    return JsonResponse(events, safe=False)

# ------------------------------
# แสดงรายการครุภัณฑ์ สำหรับยืม
# ------------------------------
@login_required
def loan_list(request):
    # เริ่มต้นด้วยการ query ครุภัณฑ์ทั้งหมด
    asset_items_query = AssetItemLoan.objects.all()
    
    has_line_account = False
    if request.user.is_authenticated:
        # UserLine_Asset.objects.filter(user=request.user).exists()
        # หรือใช้ try: request.user.userline_asset
        
        # สมมติว่าคุณต้องการให้แต่ละ MyUser มี UserLine_Asset ได้หลายรายการ
        # ถ้าต้องการแค่รายการเดียว (ควรใช้ OneToOneField แทน) สามารถใช้ try-except ได้
        
        # วิธีที่แนะนำสำหรับ ForeignKey:
        has_line_account = UserLine_Asset.objects.filter(user=request.user).exists()

    # Prefetch ข้อมูลการจองล่าสุด
    asset_items_query = asset_items_query.prefetch_related(
        Prefetch('assetreservation_set',
                 queryset=AssetReservation.objects.order_by('reserved_date'),
                 to_attr='current_reservation')
    )
    
    query = request.GET.get("q", "")
    category_id = request.GET.get("category")
    subcategory_id = request.GET.get("subcategory")
    
    if query:
        asset_items_query = asset_items_query.filter(
            Q(item_name__icontains=query) |
            Q(asset_code__icontains=query)
        )

    selected_category = None
    if category_id:
        selected_category = get_object_or_404(AssetCategory, id=category_id)
        asset_items_query = asset_items_query.filter(subcategory__category=selected_category)

    selected_subcategory = None
    if subcategory_id:
        selected_subcategory = get_object_or_404(Subcategory, id=subcategory_id)
        asset_items_query = asset_items_query.filter(subcategory=selected_subcategory)
        
    asset_items = asset_items_query.all()

    context = {
        "asset_items": asset_items,
        "categories": AssetCategory.objects.all(),
        "subcategories": Subcategory.objects.all(),
        "selected_category": selected_category,
        "selected_subcategory": selected_subcategory,
        "query": query,
        'has_line_account': has_line_account,
    }
    return render(request, "loan_list.html", context)


# ------------------------------
# แสดงตะกร้า
# ------------------------------
@login_required
def loan_cart(request):
    asset_items = AssetItemLoan.objects.filter(status_borrowing=True)

    context = {
        "asset_items": asset_items
    }
    return render(request, "loan_cart.html", context)


# ------------------------------
# แสดงรายละเอียดครุภัณฑ์
# ------------------------------
@login_required
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
        # ✅ ดึง asset_ids จาก form (กัน error ถ้าไม่มีค่า)
        asset_ids_str = request.POST.get("asset_ids", "").strip()
        asset_ids = [int(i) for i in asset_ids_str.split(",") if i.isdigit()]

        # ✅ ดึง assets ที่เลือกมา
        assets_in_cart = AssetItemLoan.objects.filter(id__in=asset_ids)

        if not assets_in_cart.exists():
            messages.error(request, "ไม่มีครุภัณฑ์ในตะกร้า")
            return redirect("assets:loan_list")

        # ✅ ใช้ฟอร์มตรวจสอบข้อมูล
        form = LoanForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.status = "pending"
            order.save()

            # ✅ สร้างความสัมพันธ์กับครุภัณฑ์
            for asset in assets_in_cart:
                IssuingAssetLoan.objects.create(order_asset=order, asset=asset)
                asset.status_assetloan = True
                asset.save(update_fields=["status_assetloan"])  # save เฉพาะ field ที่เปลี่ยน

            # 🔔 แจ้งเตือนผ่าน LINE
            try:
                notify_admin_assetloan(request, order.id)
            except Exception as e:
                messages.warning(request, f"บันทึกสำเร็จ แต่ส่ง LINE ไม่ได้: {e}")

            messages.success(request, "ส่งคำขอยืมครุภัณฑ์เรียบร้อย")
            return redirect("assets:loan_list")
        else:
            # ✅ Debug form errors (กันงง)
            messages.error(request, f"ฟอร์มไม่ถูกต้อง: {form.errors.as_json()}")

    # ถ้าไม่ใช่ POST กลับหน้าเดิม
    return redirect("assets:loan_list")


# ------------------------------
# ฟังก์ชันจอง
# ------------------------------
@login_required
def reserve_asset_item(request, pk):
    asset_item = get_object_or_404(AssetItemLoan, pk=pk)
    
    # ตรวจสอบว่าครุภัณฑ์ถูกยืมอยู่หรือไม่ (ใช้ logic เดิม)
    if not asset_item.status_assetloan:
        messages.error(request, "ครุภัณฑ์นี้ไม่ได้ถูกยืมอยู่ ไม่สามารถจองได้")
        return redirect('assets:loan_list')
    
    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            reserved_date = form.cleaned_data['reserved_date']
            returning_date = form.cleaned_data['returning_date']

            # --- โค้ดที่ต้องเพิ่ม: ตรวจสอบการจองซ้ำ ---
            conflicting_reservations = AssetReservation.objects.filter(
                asset=asset_item,
                reserved_date__lt=returning_date,
                returning_date__gt=reserved_date
            )

            if conflicting_reservations.exists():
                messages.error(request, "ไม่สามารถจองได้ เนื่องจากมีผู้อื่นจองครุภัณฑ์นี้ในช่วงเวลาดังกล่าวแล้ว")
                return redirect('assets:loan_list')
            # --- จบโค้ดตรวจสอบ ---

            reservation = form.save(commit=False)
            reservation.asset = asset_item
            reservation.user = request.user
            reservation.save()
            messages.success(request, f"คุณได้ทำการจอง '{asset_item.item_name}' เรียบร้อยแล้ว")
            return redirect("assets:loan_list")
    else:
        form = ReservationForm()
    
    context = {
        'form': form,
        'asset_item': asset_item,
    }
    return render(request, "reserve_modal.html", context)

# ------------------------------
# ฟังก์ชันแยกที่คำนวณจำนวนรายการที่รออนุมัติ
# ------------------------------
def count_pending_asset_loans():
    """
    นับจำนวนออเดอร์ยืมครุภัณฑ์ที่รอการอนุมัติ (รวมรออนุมัติยืมและรออนุมัติคืน)
    """
    
    # ใช้ Q object ตามที่คุณกำหนด
    return OrderAssetLoan.objects.filter(
        Q(status='pending') | Q(status='returned_pending')
    ).count()

# ------------------------------
# ฟังก์อนุมัติคืน หน้าออเดอร์เจ้าหน้าที่
# ------------------------------
@login_required
def loan_approval_list(request):
    month = request.GET.get('month', timezone.now().month)
    year = request.GET.get('year', timezone.now().year)

    # เพิ่มการรับค่าการค้นหา 'q'
    query = request.GET.get('q', '')

    # loans = OrderAssetLoan.objects.filter(month=month, year=year)
    loans = OrderAssetLoan.objects.filter(month=month, year=year).order_by('-id')

    # เพิ่มเงื่อนไขการค้นหา
    if query:
        loans = loans.filter(
            Q(id__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(items__asset__item_name__icontains=query)
            # Q(items__asset__asset_code__icontains=query)
        ).distinct()

    loans = loans.order_by('-id')

    months = [(1,'มกราคม'),(2,'กุมภาพันธ์'),(3,'มีนาคม'),(4,'เมษายน'),
              (5,'พฤษภาคม'),(6,'มิถุนายน'),(7,'กรกฎาคม'),(8,'สิงหาคม'),
              (9,'กันยายน'),(10,'ตุลาคม'),(11,'พฤศจิกายน'),(12,'ธันวาคม')]
    years = range(2020, timezone.now().year+2)

    if request.method == "POST":
        # ใช้สำหรับ modal submit
        loan_id = request.POST.get("loan_id")
        loan = get_object_or_404(OrderAssetLoan, pk=loan_id)

        # ตรวจสอบสถานะ
        if loan.status != "returned_pending":
            messages.warning(request, "ไม่สามารถอนุมัติการคืนได้")
            return redirect("assets:loan_approval_list")

        status_return = request.POST.get("status_return")
        receiver_note = request.POST.get("receiver_note")

        loan.status = "returned"
        loan.status_return = status_return or "not_damaged"
        loan.received_by = request.user.get_full_name()
        loan.receiver_position = getattr(request.user.profile, "position", "")
        loan.confirm_received = True
        loan.receiver_note = receiver_note
        loan.date_received = timezone.now()
        loan.save()

        # คืนสถานะครุภัณฑ์ และสร้างออเดอร์อัตโนมัติถ้ามีการจอง
        for issuing in loan.items.all():
            asset = issuing.asset
            next_reservation = AssetReservation.objects.filter(asset=asset).order_by('reserved_date').first()
            if next_reservation:
                auto_loan_order = OrderAssetLoan.objects.create(
                    user=next_reservation.user,
                    date_of_use=next_reservation.reserved_date,
                    date_due=next_reservation.returning_date,
                    status="pending",
                    note=f"การยืมอัตโนมัติจากการจอง: {next_reservation.notes}"
                )
                IssuingAssetLoan.objects.create(order_asset=auto_loan_order, asset=asset)

                # ✅ แจ้งเตือนเจ้าหน้าที่เมื่อมีการสร้างออเดอร์อัตโนมัติ
                notify_admin_on_auto_loan(auto_loan_order)
                
                next_reservation.delete()
            else:
                asset.status_assetloan = False
                asset.save()

        messages.success(request, f"อนุมัติการคืน Order #{loan.id} เรียบร้อยแล้ว")

        # ✅ เพิ่มส่วนนี้: เรียกฟังก์ชันแจ้งเตือนผู้ยืมเมื่ออนุมัติการคืน
        notify_borrower(loan, action_type="returned")

        return redirect("assets:loan_approval_list")
    
    # Pagination
    paginator = Paginator(loans, 15)  # แสดง 15 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    context = {
        "page_obj": page_obj,
        "months": months,
        "years": years,
        "selected_month": int(month),
        "selected_year": int(year),
        "get_params": request.GET.copy(),  # เก็บ GET params สำหรับ pagination
        "query": query,
        "loan_pending_count": count_pending_asset_loans(), 

    }
    return render(request, "loan_approval_list.html", context)

# ------------------------------
# ฟังก์บันทึกการคืน หน้าออเดอร์ผู้ใช้งาน 
# ------------------------------
@login_required
def loan_orders_user(request):
    """
    หน้าแสดงรายการคำขออนุมัติการยืมและคืนครุภัณฑ์
    """
    now = datetime.now()
    
    # ดึงค่าเดือนและปีจาก GET parameter หรือใช้ค่าปัจจุบันเป็นค่าเริ่มต้น
    month = int(request.GET.get('month', now.month))
    year_buddhist = int(request.GET.get('year', now.year + 543))
    
    # แปลงปี พ.ศ. เป็น ค.ศ. สำหรับการค้นหาในฐานข้อมูล
    year_ad = year_buddhist - 543

    # เพิ่มโค้ดสำหรับดึงค่าค้นหา 'q'
    query = request.GET.get('q', '')

    # ดึงรายการคำขออนุมัติและรออนุมัติการคืนทั้งหมดที่มีสถานะและเดือน/ปีตรงกับที่เลือก
    # และเรียงลำดับจากใหม่ไปเก่า
    qs = OrderAssetLoan.objects.filter(
        user=request.user, # บรรทัดนี้คือส่วนสำคัญที่เพิ่มเข้ามา
        month=month,
        year=year_ad
    ).order_by('-date_created')

    # แก้ไขส่วนการค้นหาที่ถูกต้องตามโครงสร้างโมเดล
    if query:
        qs = qs.filter(
            Q(id__icontains=query) 
        ).distinct()
    
    # เรียงลำดับจากใหม่ไปเก่าหลังจากกรองแล้ว
    qs = qs.order_by('-date_created')

    # Pagination
    paginator = Paginator(qs, 15)  # แสดง 15 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'selected_month': month,
        'query': query,
        'selected_year': year_buddhist,
        'years': range(2020 + 543, datetime.now().year + 1 + 543),
        'months': [
            (1, 'มกราคม'), (2, 'กุมภาพันธ์'), (3, 'มีนาคม'), (4, 'เมษายน'),
            (5, 'พฤษภาคม'), (6, 'มิถุนายน'), (7, 'กรกฎาคม'), (8, 'สิงหาคม'),
            (9, 'กันยายน'), (10, 'ตุลาคม'), (11, 'พฤศจิกายน'), (12, 'ธันวาคม')
        ],
        # 'month_name' เป็นฟังก์ชันที่ต้องมีใน utils.py
        'month_name': thai_month_name(month),
    }
    return render(request, 'loan_orders_user.html', context)


# ------------------------------
# ฟังก์อนุมัติ/ปฏิเสธการยืม 
# ------------------------------
@login_required
def loan_approval(request, pk):
    loan = get_object_or_404(OrderAssetLoan, pk=pk)

    if request.method == "POST":
        action = request.POST.get("status")

        # กรณีอนุมัติการยืม
        if action == "approved" and loan.status == "pending":
            loan.status = "approved"
            loan.date_approved = timezone.now()

            loan.approved_by = request.user.get_full_name()
            if hasattr(request.user, "profile"):
                loan.approver_position = request.user.profile.position
            else:
                loan.approver_position = ""

            loan.save()
            messages.success(request, "อนุมัติการยืมเรียบร้อยแล้ว ✅")
            
            # ✅ เรียกใช้ฟังก์ชันแจ้งเตือนเมื่ออนุมัติ
            notify_borrower(loan, action_type="approved")

        # กรณีปฏิเสธการยืม
        elif action == "rejected" and loan.status == "pending":
            loan.status = "rejected"
            loan.date_updated = timezone.now()

            loan.approved_by = request.user.get_full_name()
            if hasattr(request.user, "profile"):
                loan.approver_position = request.user.profile.position
            else:
                loan.approver_position = ""

            note_text = request.POST.get("note", "")
            if note_text:
                loan.note = f"หมายเหตุการปฏิเสธ: {note_text}"

            loan.save()

            for issuing in loan.items.all():
                asset = issuing.asset
                next_reservation = AssetReservation.objects.filter(asset=asset).order_by("reserved_date").first()

                if next_reservation:
                    auto_loan_order = OrderAssetLoan.objects.create(
                        user=next_reservation.user,
                        date_of_use=next_reservation.reserved_date,
                        date_due=next_reservation.returning_date,
                        status="pending",
                        note=f"การยืมอัตโนมัติจากการจอง (หลังปฏิเสธ): {next_reservation.notes or ''}"
                    )
                    IssuingAssetLoan.objects.create(order_asset=auto_loan_order, asset=asset)
                    next_reservation.delete()
                else:
                    asset.status_assetloan = False
                    asset.save()

            messages.error(request, "ปฏิเสธการยืมเรียบร้อยแล้ว ❌")
            
            # ✅ เรียกใช้ฟังก์ชันแจ้งเตือนเมื่อปฏิเสธ
            notify_borrower(loan, action_type="rejected")

        else:
            messages.warning(request, "ไม่สามารถทำรายการนี้ได้")

    return redirect("assets:loan_approval_list")



# ------------------------------
# ฟังก์บันทึกส่งคืน
# ------------------------------
@login_required
def loan_approval_user(request, pk):
    loan = get_object_or_404(OrderAssetLoan, pk=pk)

    if request.method == "POST":
        action = request.POST.get("status")

        # ✅ ส่งคืนครุภัณฑ์
        if action == "returned_pending":
            loan.status = "returned_pending"
            loan.returned_by = loan.user.get_full_name()  # หรือ loan.user.username
            loan.date_returned = timezone.now()
            loan.save()

            # ✅ แจ้งเตือนเจ้าหน้าที่เมื่อมีการบันทึกการคืน
            notify_admin_on_return(loan)
            
            messages.success(request, f"คุณได้ส่งคืนครุภัณฑ์ Order #{loan.id} เรียบร้อยแล้ว")

        # ✅ ยกเลิกการยืม
        elif action == "cancel":
            loan.status = "cancel"
            loan.save()

            # ตรวจสอบว่ามีรายการจองอยู่หรือไม่
            issued_items = loan.items.all()
            for item in issued_items:
                asset = item.asset
                next_reservation = AssetReservation.objects.filter(asset=asset).order_by('reserved_date').first()
                if next_reservation:
                    # สร้างออเดอร์อัตโนมัติ
                    auto_loan_order = OrderAssetLoan.objects.create(
                        user=next_reservation.user,
                        date_of_use=next_reservation.reserved_date,
                        date_due=next_reservation.returning_date,
                        status="pending",  # รออนุมัติ
                        note=f"การยืมอัตโนมัติจากการจอง: {next_reservation.notes}"
                    )
                    IssuingAssetLoan.objects.create(order_asset=auto_loan_order, asset=asset)

                    # ✅ แจ้งเตือนเจ้าหน้าที่เมื่อมีการสร้างออเดอร์อัตโนมัติ
                    notify_admin_on_auto_loan(auto_loan_order)

                    # ลบการจอง
                    next_reservation.delete()
                else:
                    # ถ้าไม่มีการจองต่อไป ตั้งสถานะ asset เป็นว่าง
                    asset.status_assetloan = False
                    asset.save()

            messages.success(request, f"Order #{loan.id} ถูกยกเลิกเรียบร้อยแล้ว และตรวจสอบสถานะการจอง/ครุภัณฑ์แล้ว")

        return redirect("assets:loan_orders_user")

    return redirect("assets:loan_orders_user")



# ------------------------------
# ฟังก์อนุมัติการคืน สำหรับเจ้าหน้าที่
# ------------------------------
@login_required
def approve_return(request, loan_id):
    loan = get_object_or_404(OrderAssetLoan, pk=loan_id)

    if loan.status != "returned_pending":
        messages.warning(request, "ไม่สามารถอนุมัติการคืนได้")
        return redirect("assets:loan_approval_list")

    if request.method == "POST":
        status_return = request.POST.get("status_return")
        receiver_note = request.POST.get("receiver_note")

        # อัพเดทข้อมูลการคืน
        loan.status = "returned"
        loan.status_return = status_return or "not_damaged"
        loan.received_by = request.user.get_full_name()
        loan.receiver_position = getattr(request.user, "position", "")
        loan.confirm_received = True
        loan.receiver_note = receiver_note
        loan.date_received = timezone.now()
        loan.save()

        # คืนสถานะครุภัณฑ์
        for issuing in loan.items.all():
            asset = issuing.asset
            next_reservation = AssetReservation.objects.filter(asset=asset).order_by('reserved_date').first()
            if next_reservation:
                # สร้างออเดอร์อัตโนมัติ
                auto_loan_order = OrderAssetLoan.objects.create(
                    user=next_reservation.user,
                    date_of_use=next_reservation.reserved_date,
                    date_due=next_reservation.returning_date,
                    status="pending",
                    note=f"การยืมอัตโนมัติจากการจอง: {next_reservation.notes}"
                )
                IssuingAssetLoan.objects.create(order_asset=auto_loan_order, asset=asset)

                # ✅ แจ้งเตือนเจ้าหน้าที่เมื่อมีการสร้างออเดอร์อัตโนมัติ
                notify_admin_on_auto_loan(auto_loan_order)

                next_reservation.delete()
            else:
                # ไม่มีการจองต่อไป
                asset.status_assetloan = False
                asset.save()

        messages.success(request, f"อนุมัติการคืน Order #{loan.id} เรียบร้อยแล้ว")
        return redirect("assets:loan_approval_list")
    return redirect("assets:loan_approval_list")



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
