from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from assets.models import AssetCode, AssetItem, AssetCheck, AssetLoan, StorageLocation, AssetCategory, Subcategory, StorageLocation
from .forms import AssetCheckForm, AssetCodeForm, AssetItemForm, AssetLoanApprovalForm, AssetLoanForm, AssetOwnershipForm, CategoryForm, SubcategoryForm, StorageLocationForm,StorageLocationForm
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
import qrcode
from django.http import JsonResponse
from django.db import transaction
from io import BytesIO
from datetime import date
from django.core.files.base import ContentFile
from datetime import datetime, timedelta


# Create your views here.
# def base(request):
# 	return render(request, 'base_sidebar.html')

def home_assets(request):
    return render(request, 'home_assets.html')


# def repair_report(request):
#     return render(request, 'repair_report.html')



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


# บันทึกรายการครุภัณฑ์
# def add_asset_item(request):
#     categories = Category.objects.prefetch_related("subcategories").all()

#     if request.method == "POST":
#         asset_code_form = AssetCodeForm(request.POST)
#         asset_item_form = AssetItemForm(request.POST, request.FILES)

#         if asset_code_form.is_valid() and asset_item_form.is_valid():
#             try:
#                 # ดึงหรือสร้างรหัสครุภัณฑ์ใหม่
#                 asset_code, created = AssetCode.objects.get_or_create(
#                     asset_type=asset_code_form.cleaned_data["asset_type"],
#                     asset_kind=asset_code_form.cleaned_data["asset_kind"],
#                     asset_character=asset_code_form.cleaned_data["asset_character"],
#                     serial_year=asset_code_form.cleaned_data["serial_year"],
#                 )

#                 # ผูก asset_code เข้ากับรายการ
#                 asset_item = asset_item_form.save(commit=False)
#                 asset_item.asset_code = asset_code
                
#                 # คำนวณค่าความเสื่อมก่อนบันทึก
#                 if asset_item.lifetime > 0:
#                     asset_item.annual_depreciation = asset_item.purchase_price / asset_item.lifetime
                
#                 asset_item.save()

#                 # สร้างและบันทึก QR Code หลังจากที่บันทึก asset_item แล้ว (เพื่อจะได้ id)
#                 asset_item.generate_qr_code()
#                 asset_item.save() # บันทึกอีกครั้งเพื่อเก็บชื่อไฟล์ QR Code

#                 messages.success(request, "✅ บันทึกรายการครุภัณฑ์เรียบร้อยแล้ว")
#                 return redirect("assets:asset_list")

#             except Exception as e:
#                 messages.error(request, f"❌ เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")
                
#         else:
#             messages.error(request, "❌ กรุณาตรวจสอบความถูกต้องของข้อมูลในฟอร์ม")
    
#     else:
#         asset_code_form = AssetCodeForm()
#         asset_item_form = AssetItemForm()

#     return render(request, "add_asset_item.html", {
#         "asset_code_form": asset_code_form,
#         "asset_item_form": asset_item_form,
#         "categories": categories,
#     })

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

# ------------------------------------------------------------------------------------------------------------------------------------


# # แก้ไขฟังก์ชัน loan_list
# # ---- loan_list ----
# @login_required
# def loan_list(request):
#     query = request.GET.get('q', '')
#     category_id = request.GET.get('category')
#     subcategory_id = request.GET.get('subcategory')
#     page = request.GET.get('page', 1)

#     # ✅ เลือกเฉพาะที่ “ยืมได้”
#     assets = (
#         AssetItem.objects
#         .filter(status_borrowing=True)
#         .select_related('subcategory', 'subcategory__category', 'asset_code')
#         .order_by('id')
#     )

#     selected_category = None
#     selected_subcategory = None

#     if query:
#         assets = assets.filter(item_name__icontains=query)

#     if category_id:
#         selected_category = get_object_or_404(AssetCategory, id=category_id)
#         assets = assets.filter(subcategory__category=selected_category)

#     if subcategory_id:
#         selected_subcategory = get_object_or_404(Subcategory, id=subcategory_id)
#         assets = assets.filter(subcategory=selected_subcategory)

#     p = Paginator(assets, 10)
#     try:
#         asset_items = p.page(page)
#     except PageNotAnInteger:
#         asset_items = p.page(1)
#     except EmptyPage:
#         asset_items = p.page(p.num_pages)

#     # ✅ ใช้ session เป็น list ของ id (int)
#     cart_asset_ids = [int(x) for x in request.session.get('cart', [])]
#     assets_in_cart = (
#         AssetItem.objects
#         .filter(id__in=cart_asset_ids)
#         .select_related('asset_code')
#     )

#     categories = AssetCategory.objects.all()
#     subcategories = Subcategory.objects.filter(category=selected_category) if selected_category else []
    
#     context = {
#         'asset_items': asset_items,
#         'query': query,
#         'selected_category': selected_category,
#         'selected_subcategory': selected_subcategory,
#         'categories': categories,
#         'subcategories': subcategories,
#         'assets_in_cart': assets_in_cart,
#         'cart_count': len(cart_asset_ids),   # ✅ จุดที่เพิ่ม
        
#     }
#     return render(request, 'loan_list.html', context)


# # ---- add_to_cart ----
# @login_required
# def add_to_cart(request, asset_id):
#     cart = request.session.get('cart', [])
#     if not isinstance(cart, list):
#         cart = []

#     if len(cart) >= 5:
#         messages.error(request, 'ไม่สามารถเพิ่มรายการได้เกิน 5 รายการในตะกร้า!')
#         return redirect('assets:loan_list')

#     if int(asset_id) in cart:
#         messages.info(request, 'ครุภัณฑ์นี้อยู่ในตะกร้าแล้ว')
#         return redirect('assets:loan_list')

#     asset = get_object_or_404(AssetItem, id=asset_id)
#     if asset.status_assetloan:
#         messages.error(request, f'ครุภัณฑ์ "{asset.item_name}" ไม่พร้อมให้ยืมในขณะนี้')
#         return redirect('assets:loan_list')   # ✅ แก้เป็น loan_list

#     cart.append(int(asset_id))
#     request.session['cart'] = cart
#     request.session.modified = True
#     messages.success(request, 'เพิ่มครุภัณฑ์ลงในตะกร้าเรียบร้อยแล้ว')
#     return redirect('assets:loan_list')


# # ---- remove_from_cart ----
# @login_required
# def remove_from_cart(request, asset_id):
#     cart = request.session.get('cart', [])
#     if not isinstance(cart, list):
#         cart = []

#     try:
#         cart.remove(int(asset_id))
#         request.session['cart'] = cart
#         request.session.modified = True
#         messages.success(request, 'ลบครุภัณฑ์ออกจากตะกร้าเรียบร้อยแล้ว')
#     except (ValueError, TypeError):
#         messages.error(request, 'ไม่พบรายการครุภัณฑ์ที่ต้องการลบ')

#     return redirect('assets:loan_list')


# # ---- confirm_loan ----
# @login_required
# def confirm_loan(request):
#     cart_asset_ids = [int(x) for x in request.session.get("cart", [])]
#     if not cart_asset_ids:
#         messages.error(request, 'ไม่มีครุภัณฑ์ในตะกร้า')
#         return redirect('assets:loan_list')

#     assets_to_loan = AssetItem.objects.filter(id__in=cart_asset_ids)

#     with transaction.atomic():
#         for asset in assets_to_loan:
#             AssetLoan.objects.create(
#                 asset=asset,
#                 user=request.user,
#                 date_due=datetime.now().date() + timedelta(days=7),
#                 status='pending'
#             )
#             asset.status_assetloan = True
#             asset.save(update_fields=['status_assetloan'])

#     request.session['cart'] = []  # ✅ เคลียร์ตะกร้า
#     request.session.modified = True

#     messages.success(request, 'ส่งคำขอยืมสำเร็จแล้ว!')
#     return redirect('assets:loan_list')




@login_required
def loan_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    subcategory_id = request.GET.get('subcategory')
    page = request.GET.get('page', 1)

    # ✅ เลือกเฉพาะที่ “ยืมได้” ตามฟิลด์ของคุณ: status_borrowing=True
    qs = (
        AssetItem.objects
        .filter(status_borrowing=True)  # พร้อมให้ยืม
        .select_related('subcategory', 'subcategory__category', 'asset_code')
        .order_by('id')
    )

    selected_category = None
    selected_subcategory = None

    if query:
        qs = qs.filter(item_name__icontains=query)

    if category_id:
        selected_category = get_object_or_404(AssetCategory, id=category_id)
        qs = qs.filter(subcategory__category=selected_category)

    if subcategory_id:
        selected_subcategory = get_object_or_404(Subcategory, id=subcategory_id)
        qs = qs.filter(subcategory=selected_subcategory)

    p = Paginator(qs, 10)
    try:
        asset_items = p.page(page)
    except PageNotAnInteger:
        asset_items = p.page(1)
    except EmptyPage:
        asset_items = p.page(p.num_pages)

    # ✅ ใช้ session เป็น list ของ id (int)
    cart = request.session.get('cart', [])
    if not isinstance(cart, list):
        cart = []
    cart_asset_ids = [int(x) for x in cart]

    assets_in_cart = AssetItem.objects.filter(id__in=cart_asset_ids).select_related('asset_code')

    categories = AssetCategory.objects.all()
    subcategories = Subcategory.objects.filter(category=selected_category) if selected_category else Subcategory.objects.none()

    context = {
        'asset_items': asset_items,
        'query': query,
        'selected_category': selected_category,
        'selected_subcategory': selected_subcategory,
        'categories': categories,
        'subcategories': subcategories,
        'assets_in_cart': assets_in_cart,
        'cart_count': len(cart_asset_ids),
    }
    # ✅ context เป็น dict แน่นอน แก้ปัญหา "'list' object has no attribute 'items'"
    print("DEBUG CONTEXT:", type(context), context)  # 👈 เพิ่มบรรทัดนี้ก่อน return
    # ในฟังก์ชัน loan_list ของคุณ
    print("Cart session at start of view:", request.session.get('cart'))
    if 'test_data' not in request.session:
        request.session['test_data'] = 'test_value'
        request.session.modified = True
        print("Session modified")
    else:
        print("Session already has test_data")

    # บรรทัดนี้ควรแสดงข้อมูลตะกร้าที่ถูกต้อง หาก session ทำงาน
    print("Cart session at end of view:", request.session.get('cart'))
    return render(request, 'loan_list.html', context)


# ================= AJAX เพิ่ม/ลบตะกร้า =================
@login_required
def add_to_cart_ajax(request):
    if request.method == "POST":
        asset_id = request.POST.get("asset_id")
        cart = request.session.get("cart", [])
        if not isinstance(cart, list):
            cart = []

        try:
            asset_id = int(asset_id)
            if asset_id not in cart:
                asset = AssetItem.objects.select_related('asset_code').get(id=asset_id)
                cart.append(asset_id)
                request.session["cart"] = cart
                request.session.modified = True
                
                # ✅ เพิ่มข้อมูล asset ที่จำเป็นเข้าไปใน JsonResponse
                return JsonResponse({
                    "success": True, 
                    "cart_count": len(cart),
                    "asset_id": asset.id,
                    "asset_name": asset.item_name,
                    "asset_code": str(asset.asset_code),  # แปลงเป็น str เพื่อให้แสดงผลได้
                })
        except (ValueError, AssetItem.DoesNotExist):
            return JsonResponse({"success": False, "message": "ไม่พบรายการครุภัณฑ์"})
            
        return JsonResponse({"success": False, "message": "ครุภัณฑ์นี้อยู่ในตะกร้าแล้ว"})
    return JsonResponse({"success": False, "message": "วิธีเรียกไม่ถูกต้อง"})


@login_required
def remove_from_cart_ajax(request):
    if request.method == "POST":
        asset_id = request.POST.get("asset_id")
        cart = request.session.get("cart", [])
        if not isinstance(cart, list):
            cart = []
        try:
            cart.remove(int(asset_id))
            request.session["cart"] = cart
            request.session.modified = True
            return JsonResponse({"success": True, "cart_count": len(cart)})
        except (ValueError, TypeError):
            return JsonResponse({"success": False, "message": "ไม่พบรายการครุภัณฑ์"})
    return JsonResponse({"success": False, "message": "วิธีเรียกไม่ถูกต้อง"})


@login_required
def confirm_loan(request):
    if request.method != 'POST':
        messages.error(request, 'วิธีส่งคำขอไม่ถูกต้อง')
        return redirect('assets:loan_list')

    cart_asset_ids = [int(x) for x in request.session.get("cart", [])]
    if not cart_asset_ids:
        messages.error(request, 'ไม่มีครุภัณฑ์ในตะกร้า')
        return redirect('assets:loan_list')

    assets_to_loan = AssetItem.objects.filter(id__in=cart_asset_ids)

    with transaction.atomic():
        for asset in assets_to_loan:
            AssetLoan.objects.create(
                asset=asset,
                user=request.user,
                date_due=datetime.now().date() + timedelta(days=7),
                status='pending'
            )
            asset.status_assetloan = True
            asset.save(update_fields=['status_assetloan'])

    request.session['cart'] = []
    request.session.modified = True

    messages.success(request, 'ส่งคำขอยืมสำเร็จแล้ว!')
    return redirect('assets:loan_list')


# @login_required
# def add_to_cart(request, asset_id):
#     # ✅ cart เป็น list เสมอ
#     cart = request.session.get('cart', [])
#     if not isinstance(cart, list):
#         cart = []

#     # จำกัดจำนวนไม่เกิน 5
#     if len(cart) >= 5:
#         messages.error(request, 'ไม่สามารถเพิ่มรายการได้เกิน 5 รายการในตะกร้า!')
#         return redirect('assets:loan_list')  # ✅ ชื่อ url name ตรงกับ urls.py

#     # ไม่ให้ซ้ำ
#     if int(asset_id) in [int(x) for x in cart]:
#         messages.info(request, 'ครุภัณฑ์นี้อยู่ในตะกร้าแล้ว')
#         return redirect('assets:loan_list')

#     # ตรวจสถานะ
#     asset = get_object_or_404(AssetItem, id=asset_id)
#     if asset.status_assetloan:
#         messages.error(request, f'ครุภัณฑ์ "{asset.item_name}" ไม่พร้อมให้ยืมในขณะนี้')
#         return redirect('assets:loan_list')  # ✅ ห้ามใช้ loan-list

#     cart.append(int(asset_id))
#     request.session['cart'] = cart
#     request.session.modified = True
#     messages.success(request, 'เพิ่มครุภัณฑ์ลงในตะกร้าเรียบร้อยแล้ว')
#     return redirect('assets:loan_list')


# @login_required
# def remove_from_cart(request, asset_id):
#     cart = request.session.get('cart', [])
#     if not isinstance(cart, list):
#         cart = []
#     try:
#         cart.remove(int(asset_id))
#         request.session['cart'] = cart
#         request.session.modified = True
#         messages.success(request, 'ลบครุภัณฑ์ออกจากตะกร้าเรียบร้อยแล้ว')
#     except (ValueError, TypeError):
#         messages.error(request, 'ไม่พบรายการครุภัณฑ์ที่ต้องการลบ')
#     return redirect('assets:loan_list')


# @login_required
# def confirm_loan(request):
#     # ✅ รองรับเฉพาะ POST เพื่อความถูกต้อง
#     if request.method != 'POST':
#         messages.error(request, 'วิธีส่งคำขอไม่ถูกต้อง')
#         return redirect('assets:loan_list')

#     cart_asset_ids = [int(x) for x in request.session.get("cart", [])]
#     if not cart_asset_ids:
#         messages.error(request, 'ไม่มีครุภัณฑ์ในตะกร้า')
#         return redirect('assets:loan_list')

#     assets_to_loan = AssetItem.objects.filter(id__in=cart_asset_ids)

#     with transaction.atomic():
#         for asset in assets_to_loan:
#             # ✅ ถ้ามีโมเดลชื่ออื่น ใช้ชื่อโมเดลจริงแทน AssetLoan
#             AssetLoan.objects.create(
#                 asset=asset,
#                 user=request.user,
#                 date_due=datetime.now().date() + timedelta(days=7),
#                 status='pending'
#             )
#             # set เป็นยืมอยู่
#             asset.status_assetloan = True
#             asset.save(update_fields=['status_assetloan'])

#     # ✅ ล้างตะกร้า
#     request.session['cart'] = []
#     request.session.modified = True

#     messages.success(request, 'ส่งคำขอยืมสำเร็จแล้ว!')
#     return redirect('assets:loan_list')












# ฟังก์ชัน loan_list ที่ได้รับการแก้ไขและรวมการทำงานทั้งหมด
# @login_required
# def loan_list(request):
#     query = request.GET.get('q', '')
#     category_id = request.GET.get('category')
#     subcategory_id = request.GET.get('subcategory')  
#     page = request.GET.get('page', 1)

#     # เริ่มต้น QuerySet โดยกรองเฉพาะรายการที่ status_borrowing=True
#     assets = AssetItem.objects.filter(status_borrowing=True).select_related('subcategory__category').order_by('id')

#     # ตัวแปรสำหรับใช้ใน template
#     selected_category = None
#     selected_subcategory = None
    
#     # กรองข้อมูลตามคำค้นหา
#     if query:
#         assets = assets.filter(item_name__icontains=query)

#     # กรองข้อมูลตามหมวดหมู่หลัก
#     if category_id:
#         try:
#             selected_category = get_object_or_404(AssetCategory, id=category_id)
#             assets = assets.filter(subcategory__category=selected_category)
#         except:
#             messages.error(request, 'ไม่พบหมวดหมู่ที่ต้องการ')
#             return redirect('assets:loan-list')

#     # กรองข้อมูลตามหมวดหมู่ย่อย
#     if subcategory_id:
#         try:
#             selected_subcategory = get_object_or_404(Subcategory, id=subcategory_id)
#             assets = assets.filter(subcategory=selected_subcategory)
#         except:
#             messages.error(request, 'ไม่พบหมวดหมู่ย่อยที่ต้องการ')
#             return redirect('assets:loan-list')

#     # Pagination
#     p = Paginator(assets, 10)
    
#     try:
#         asset_items = p.page(page)
#     except PageNotAnInteger:
#         asset_items = p.page(1)
#     except EmptyPage:
#         asset_items = p.page(p.num_pages)

#     # ดึงข้อมูลหมวดหมู่ทั้งหมดสำหรับเมนู
#     categories = AssetCategory.objects.all()
#     subcategories = []
#     if selected_category:
#         subcategories = Subcategory.objects.filter(category=selected_category)

#     context = {
#         'asset_items': asset_items,
#         'query': query,
#         'selected_category': selected_category,
#         'selected_subcategory': selected_subcategory,
#         'categories': categories,
#         'subcategories': subcategories,
#     }
#     return render(request, 'loan_list.html', context)


# @login_required
# def add_to_cart(request, asset_id):
#     # ตรวจสอบและทำให้แน่ใจว่า 'cart' ใน session เป็น list เสมอ
#     if 'cart' not in request.session or not isinstance(request.session['cart'], list):
#         request.session['cart'] = []

#     cart = request.session['cart']

#     if asset_id not in cart:
#         cart.append(asset_id)
#         request.session.modified = True
#         messages.success(request, 'เพิ่มครุภัณฑ์ลงในตะกร้าเรียบร้อยแล้ว')
#     else:
#         messages.info(request, 'ครุภัณฑ์นี้อยู่ในตะกร้าแล้ว')
    
#     return redirect('assets:loan-list')

# @login_required
# def remove_from_cart(request, asset_id):
#     # ตรวจสอบและทำให้แน่ใจว่า 'cart' ใน session เป็น list เสมอ
#     if 'cart' in request.session and isinstance(request.session['cart'], list):
#         cart = request.session['cart']
#         if asset_id in cart:
#             cart.remove(asset_id)
#             request.session.modified = True
#             messages.success(request, 'ลบครุภัณฑ์ออกจากตะกร้าเรียบร้อยแล้ว')

#     return redirect('assets:loan-list')

# @login_required
# def confirm_loan(request):
#     cart_asset_ids = request.session.get("cart", [])
#     if not cart_asset_ids:
#         messages.error(request, 'ไม่มีครุภัณฑ์ในตะกร้า')
#         return redirect('assets:loan-list')

#     # สร้าง LoanRequest และเพิ่มครุภัณฑ์เข้าไปใน M2M field
#     loan_request = LoanRequest.objects.create(
#         user=request.user,
#         # เพิ่มข้อมูลอื่นๆ ที่จำเป็น
#     )
#     assets_to_loan = AssetItem.objects.filter(id__in=cart_asset_ids)
#     loan_request.assets.set(assets_to_loan)

#     # เปลี่ยนสถานะครุภัณฑ์
#     for asset in assets_to_loan:
#         asset.status_assetloan = True
#         asset.save()

#     # ล้างตะกร้าใน session และบันทึกการเปลี่ยนแปลง
#     del request.session['cart']
#     request.session.modified = True

#     messages.success(request, 'ส่งคำขอยืมสำเร็จแล้ว!')
#     return redirect('assets:loan-list')


# @login_required
# def request_loan(request):
#     """ส่งคำขอยืม (แบบใช้ฟอร์มเดี่ยว ๆ)"""
#     if request.method == "POST":
#         form = AssetLoanForm(request.POST)
#         if form.is_valid():
#             loan = form.save(commit=False)
#             loan.user = request.user
#             loan.status = "pending"
#             loan.save()
#             messages.success(request, "ส่งคำขอยืมสำเร็จ รอการอนุมัติ")
#             return redirect("assets:loan-list")
#     else:
#         form = AssetLoanForm()
#     return render(request, "request_loan.html", {"form": form})


@login_required
def loan_approval_list(request):
    """
    หน้าแสดงรายการคำขออนุมัติการยืมและคืนครุภัณฑ์
    """
    # กรองคำขอที่รออนุมัติและรออนุมัติการคืน
    # qs = AssetLoan.objects.filter(status__in=['pending', 'returned_pending']).order_by('-loan_date')
    qs = AssetLoan.objects.all().order_by('-loan_date')
    
    # pagination (ไม่บังคับ แต่ช่วยให้หน้าไม่ยาวเกินไป)
    paginator = Paginator(qs, 15)  # แสดง 15 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'loan_approval_list.html', context)


@login_required
def loan_approval(request, loan_id):
    """ผู้ดูแล อนุมัติหรือปฏิเสธคำขอ"""
    loan = get_object_or_404(AssetLoan, id=loan_id)
    asset = loan.asset

    if request.method == "POST":
        form = AssetLoanApprovalForm(request.POST, instance=loan)
        if form.is_valid():
            loan = form.save(commit=False)

            if loan.status == "approved":
                # รอผู้ใช้มากดยืนยันการรับ
                messages.success(request, f"อนุมัติการยืมของ {loan.user.username} แล้ว")

            elif loan.status == "rejected":
                asset.status_assetloan = False
                messages.warning(request, f"ปฏิเสธคำขอของ {loan.user.username}")

            loan.save()
            asset.save()
            return redirect("assets:loan-approval-list")
    else:
        form = AssetLoanApprovalForm(instance=loan)

    return render(request, "loan_approval.html", {"form": form, "loan": loan})


@login_required
def confirm_receipt(request, loan_id):
    """ผู้ใช้ยืนยันการรับครุภัณฑ์"""
    loan = get_object_or_404(AssetLoan, id=loan_id, user=request.user)
    asset = loan.asset

    if loan.status == "approved" and not loan.confirm:
        loan.confirm = True
        loan.status = "borrowed"
        loan.date_received = timezone.now()
        loan.save()

        asset.status_assetloan = True  # ตอนนี้ถึงเปลี่ยนเป็นไม่ว่าง
        asset.save()

        messages.success(request, "ยืนยันรับครุภัณฑ์เรียบร้อยแล้ว")
    else:
        messages.warning(request, "ไม่สามารถยืนยันรับครุภัณฑ์ได้")

    return redirect("assets:loan-list")


@login_required
def request_return(request, loan_id):
    """ผู้ใช้แจ้งคืนครุภัณฑ์"""
    loan = get_object_or_404(AssetLoan, id=loan_id, user=request.user)

    if loan.status == "borrowed":
        loan.status = "returned_pending"
        loan.save()
        messages.success(request, "แจ้งคืนครุภัณฑ์แล้ว รอการอนุมัติ")
    else:
        messages.warning(request, "ไม่สามารถแจ้งคืนได้")

    return redirect("assets:loan-list")


@login_required
def approve_return(request, loan_id):
    """ผู้ดูแล อนุมัติการคืน"""
    loan = get_object_or_404(AssetLoan, id=loan_id)
    asset = loan.asset

    if loan.status == "returned_pending":
        loan.date_of_return = timezone.now().date()
        loan.status = "returned"
        loan.save()

        asset.status_assetloan = False
        asset.save()

        messages.success(request, f"อนุมัติการคืนของ {loan.user.username}")
    else:
        messages.warning(request, "ไม่สามารถอนุมัติการคืนได้")

    return redirect("assets:loan-approval-list")

# ฟังก์ชันค้นหา
# def search_category(request):
#     query = request.GET.get('q')
#     subcategories = Subcategory.objects.filter(name_sub__icontains=query)
#     categories = Category.objects.filter(name_cate__icontains=query)

#     return render(request, 'asset_search_results.html', {
#         'query': query,
#         'subcategories': subcategories,
#         'categories': categories,
#     })

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
    category = get_object_or_404(Category, pk=pk)
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
    category = get_object_or_404(Category, pk=pk)
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
    subcategory = get_object_or_404(Subcategory, pk=pk)
    if request.method == 'POST':
        form = SubcategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ แก้ไขหมวดหมู่ย่อยเรียบร้อยแล้ว')
            return redirect('assets:asset_list_subcate')
        else:
            messages.error(request, '❌ แก้ไขไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    else:
        form = SubategoryForm(instance=category)

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
