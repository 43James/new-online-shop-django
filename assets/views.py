
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import MyUser, Profile
from app_linebot.models import UserLine_Asset
from app_linebot.views import notify_admin_assetloan, notify_admin_on_auto_loan, notify_admin_on_return, notify_borrower, notify_overdue_asset_loan
from assets.models import AssetCheck, AssetCode, AssetItem, AssetItemLoan, AssetOwnership, AssetReservation, AssetTransferItem, AssetTransferRequest, StorageLocation, AssetCategory, Subcategory, OrderAssetLoan,IssuingAssetLoan, AssetSystemSetting
from dashboard.views import thai_month_name
from .forms import AssetCheckForm, AssetCodeForm, AssetItemForm, AssetItemLoanForm, CategoryForm, LoanForm, ReservationForm, SubcategoryForm, StorageLocationForm,StorageLocationForm
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
import json
from django.db import IntegrityError, transaction
from datetime import datetime
from django.http import JsonResponse
import json
import pandas as pd



@login_required
def home_assets(request):
    from django.db.models import Count, Sum
    
    # === สถิติรวม ===
    total_assets = AssetItem.objects.count()
    ready_assets = AssetItem.objects.filter(damage_status='ใช้งานได้').count()
    repairing_assets = AssetItem.objects.filter(damage_status='ชำรุด').count()
    broken_assets = AssetItem.objects.filter(
        damage_status__in=['เสื่อมสภาพ', 'สูญไป', 'ไม่ใช้']
    ).count()
    
    # === มูลค่ารวม ===
    total_value = AssetItem.objects.aggregate(total=Sum('purchase_price'))['total'] or 0
    
    # === สถิติตามหมวดหมู่ (สำหรับกราฟ) ===
    categories_data = AssetCategory.objects.annotate(
        asset_count=Count('subcategories__asset_items')
    ).values('name_cate', 'asset_count').order_by('-asset_count')
    
    chart_labels = [c['name_cate'] for c in categories_data]
    chart_values = [c['asset_count'] for c in categories_data]
    
    # === สถิติตามสถานที่เก็บ (สำหรับกราฟวงกลม) ===
    location_data = StorageLocation.objects.annotate(
        asset_count=Count('assetitem')
    ).filter(asset_count__gt=0).values('name', 'asset_count').order_by('-asset_count')[:8]
    
    location_labels = [l['name'] for l in location_data]
    location_values = [l['asset_count'] for l in location_data]
    
    # === รายการครุภัณฑ์ล่าสุด 5 รายการ ===
    recent_assets = AssetItem.objects.select_related(
        'asset_code', 'storage_location', 'subcategory'
    ).order_by('-date_asset_created')[:5]
    
    # === การยืมครุภัณฑ์ล่าสุด ===
    recent_loans = OrderAssetLoan.objects.select_related('user').order_by('-date_created')[:5]
    
    # === คำร้องเคลื่อนย้ายล่าสุด ===
    pending_transfers = AssetTransferRequest.objects.filter(
        status__in=['PENDING_HEAD', 'PENDING_DIRECTOR', 'PENDING_ACTION']
    ).count()
    
    # === สรุปการยืม ===
    active_loans = OrderAssetLoan.objects.filter(status__in=['borrowed', 'approved', 'overdue']).count()
    pending_loan_approvals = OrderAssetLoan.objects.filter(status='pending').count()
    overdue_loans = OrderAssetLoan.objects.filter(status='overdue').count()
    
    # === สถิติการตรวจนับครุภัณฑ์ ===
    available_check_years = AssetCheck.objects.values_list('fiscal_year', flat=True).distinct().order_by('-fiscal_year')
    current_check_year = available_check_years.first() if available_check_years.exists() else None
    
    if current_check_year and total_assets > 0:
        checked_count = AssetCheck.objects.filter(fiscal_year=current_check_year).values('asset').distinct().count()
        check_percentage = round((checked_count / total_assets) * 100, 1)
        unchecked_count = total_assets - checked_count
    else:
        checked_count = 0
        check_percentage = 0
        unchecked_count = total_assets
    
    context = {
        "loan_pending_count": count_pending_asset_loans(),
        "total_assets": total_assets,
        "ready_assets": ready_assets,
        "repairing_assets": repairing_assets,
        "broken_assets": broken_assets,
        "total_value": total_value,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "location_labels": location_labels,
        "location_values": location_values,
        "recent_assets": recent_assets,
        "recent_loans": recent_loans,
        "pending_transfers": pending_transfers,
        "active_loans": active_loans,
        "pending_loan_approvals": pending_loan_approvals,
        "overdue_loans": overdue_loans,
        "current_check_year": current_check_year,
        "checked_count": checked_count,
        "unchecked_count": unchecked_count,
        "check_percentage": check_percentage,
    }
    return render(request, 'assets/home/home_assets.html', context)



def import_assets(request):
    if request.method == 'POST' and request.FILES['excel_file']:
        excel_file = request.FILES['excel_file']
        
        # ตรวจสอบว่าเป็นไฟล์ Excel หรือไม่
        if not excel_file.name.endswith(('.xls', '.xlsx')):
            messages.error(request, 'กรุณาอัปโหลดไฟล์ Excel เท่านั้น')
            return redirect('import_assets') # เปลี่ยนเป็นชื่อ URL ของคุณ

        try:
            # อ่านไฟล์ Excel ด้วย Pandas
            df = pd.read_excel(excel_file)
            
            # แปลงชื่อคอลัมน์ให้เป็นมาตรฐาน (ลบช่องว่างหัวท้าย)
            df.columns = df.columns.str.strip()

            success_count = 0
            error_list = []

            # ใช้ transaction เพื่อความปลอดภัยของข้อมูล (ถ้าพังบรรทัดไหน ให้ rollback หรือเลือกข้ามได้)
            # ในที่นี้จะเขียนแบบข้ามบรรทัดที่ error แล้วแจ้งเตือน
            
            for index, row in df.iterrows():
                try:
                    with transaction.atomic():
                        # 1. จัดการ หมวดหมู่หลัก (AssetCategory)
                        category, _ = AssetCategory.objects.get_or_create(
                            name_cate=str(row['หมวดหมู่หลัก']).strip()
                        )

                        # 2. จัดการ หมวดหมู่ย่อย (Subcategory)
                        subcategory, _ = Subcategory.objects.get_or_create(
                            name_sub=str(row['หมวดหมู่ย่อย']).strip(),
                            category=category
                        )

                        # 3. จัดการ สถานที่เก็บ (StorageLocation)
                        location, _ = StorageLocation.objects.get_or_create(
                            name=str(row['สถานที่เก็บ']).strip()
                        )

                        raw_serial = row.get('ลำดับ/ปี')
                        if pd.isna(raw_serial) or not str(raw_serial).strip():
                            raise ValueError("ข้อมูล 'ลำดับ/ปี' ว่างเปล่าไม่ได้")
                            
                        # 4. จัดการ รหัสครุภัณฑ์ (AssetCode)
                        asset_code_obj, created = AssetCode.objects.get_or_create(
                            serial_year=str(raw_serial).strip(),
                            defaults={
                                'asset_type': str(row.get('ประเภท', '-')).strip() if pd.notna(row.get('ประเภท')) else '-',
                                'asset_kind': str(row.get('ชนิด', '-')).strip() if pd.notna(row.get('ชนิด')) else '-',
                                'asset_character': str(row.get('ลักษณะ', '-')).strip() if pd.notna(row.get('ลักษณะ')) else '-',
                            }
                        )
                        
                        if not created:
                             asset_code_obj.asset_type = str(row.get('ประเภท', '-')).strip() if pd.notna(row.get('ประเภท')) else '-'
                             asset_code_obj.asset_kind = str(row.get('ชนิด', '-')).strip() if pd.notna(row.get('ชนิด')) else '-'
                             asset_code_obj.asset_character = str(row.get('ลักษณะ', '-')).strip() if pd.notna(row.get('ลักษณะ')) else '-'
                             asset_code_obj.save()

                        # ฟังก์ชันช่วยเหลือแปลงข้อมูล
                        def safe_int(val, default=0):
                            try:
                                return int(float(val)) if pd.notna(val) else default
                            except:
                                return default
                                
                        def safe_decimal(val, default=0):
                            try:
                                return float(val) if pd.notna(val) else default
                            except:
                                return default

                        raw_date = row.get('วันที่ซื้อ')
                        if pd.isna(raw_date):
                            p_date = timezone.now().date()
                        else:
                            try:
                                p_date = pd.to_datetime(raw_date).date()
                            except:
                                p_date = timezone.now().date()

                        # 5. สร้างรายการครุภัณฑ์ (AssetItem)
                        asset_item = AssetItem(
                            asset_code=asset_code_obj,
                            item_name=str(row.get('ชื่อรายการครุภัณฑ์', 'ไม่มีชื่อ')).strip() if pd.notna(row.get('ชื่อรายการครุภัณฑ์')) else 'ไม่มีชื่อ',
                            subcategory=subcategory,
                            unit=str(row.get('หน่วยนับ', 'ชิ้น')).strip() if pd.notna(row.get('หน่วยนับ')) else 'ชิ้น',
                            purchase_price=safe_decimal(row.get('ราคาที่ซื้อ')),
                            purchase_date=p_date,
                            fiscal_year=safe_int(row.get('ปีที่ใช้งาน'), timezone.now().year),
                            lifetime=safe_int(row.get('อายุการใช้งาน'), 0),
                            used_years=safe_int(row.get('ใช้มาแล้วกี่ปี'), 0),
                            responsible_person=str(row.get('ผู้รับผิดชอบ', '-')).strip() if pd.notna(row.get('ผู้รับผิดชอบ')) else '-',
                            storage_location=location,
                            brand_model=str(row.get('ยี่ห้อ/รุ่น', '-')).strip() if pd.notna(row.get('ยี่ห้อ/รุ่น')) else '-',
                            notes=str(row.get('หมายเหตุ', '')) if pd.notna(row.get('หมายเหตุ')) else "",
                            damage_status=str(row.get('สถานะการใช้งาน', 'ใช้งานได้')).strip() if pd.notna(row.get('สถานะการใช้งาน')) else "ใช้งานได้",
                            status_borrowing=True if pd.notna(row.get('ยืมได้หรือไม่')) and str(row.get('ยืมได้หรือไม่')).lower() in ['yes', 'true', 'ได้', '1'] else False
                        )
                        
                        # เรียก save() เพื่อให้คำนวณค่าเสื่อมและสร้าง QR Code อัตโนมัติ
                        asset_item.save()
                        success_count += 1

                except Exception as e:
                    error_msg = f"Row {index + 2}: Error - {str(e)}"
                    error_list.append(error_msg)
                    continue

            # สรุปผลการทำงาน
            messages.success(request, f'บันทึกสำเร็จ {success_count} รายการ')
            if error_list:
                messages.warning(request, f'พบข้อผิดพลาด {len(error_list)} รายการ: <br>' + '<br>'.join(error_list))

        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}')

    return render(request, 'assets/items/import_assets.html')

import io
from django.http import HttpResponse

@login_required
def export_assets(request):
    assets = AssetItem.objects.select_related(
        'subcategory__category', 
        'asset_code', 
        'storage_location'
    ).all()
    
    data = []
    for index, asset in enumerate(assets, start=1):
        # คำนวณค่าเสื่อมรายวัน
        annual_depreciation = float(asset.annual_depreciation) if asset.annual_depreciation else 0
        daily_depreciation = annual_depreciation / 365 if annual_depreciation > 0 else 0
        
        data.append({
            'ลำดับ': index,
            'หมวดหมู่หลัก': asset.subcategory.category.name_cate if asset.subcategory and asset.subcategory.category else '',
            'หมวดหมู่ย่อย': asset.subcategory.name_sub if asset.subcategory else '',
            'ชื่อรายการครุภัณฑ์': asset.item_name,
            'ประเภท': asset.asset_code.asset_type if asset.asset_code else '',
            'ชนิด': asset.asset_code.asset_kind if asset.asset_code else '',
            'ลักษณะ': asset.asset_code.asset_character if asset.asset_code else '',
            'ลำดับ/ปี': asset.asset_code.serial_year if asset.asset_code else '',
            'หน่วยนับ': asset.unit,
            'ราคาที่ซื้อ': float(asset.purchase_price) if asset.purchase_price else 0,
            'วันที่ซื้อ': asset.purchase_date.strftime('%Y-%m-%d') if asset.purchase_date else '',
            'ปีที่ใช้งาน': asset.fiscal_year,
            'อายุการใช้งาน': asset.lifetime,
            'ใช้มาแล้วกี่ปี': asset.used_years,
            'ค่าความเสื่อมต่อปี': annual_depreciation,
            'ค่าเสื่อมราคาประจำปี (บาท)/วัน': daily_depreciation,
            'ผู้รับผิดชอบ': asset.responsible_person,
            'สถานที่เก็บ': asset.storage_location.name if asset.storage_location else '',
            'ยี่ห้อ/รุ่น': asset.brand_model,
            'หมายเหตุ': asset.notes if asset.notes else '',
            'สถานะการใช้งาน': asset.damage_status,
            'ยืมได้หรือไม่': 'Yes' if asset.status_borrowing else 'No'
        })
        
    df = pd.DataFrame(data)
    output = io.BytesIO()
    # openpyxl should be available since pd.read_excel works for .xlsx
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Assets')
        
    output.seek(0)
    response = HttpResponse(
        output, 
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="assets_export.xlsx"'
    return response



# รายการครุภัณฑ์
@login_required
def asset_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    location_id = request.GET.get('storage_location', '')
    status = request.GET.get('damage_status', '')

    # ดึงข้อมูลรายการครุภัณฑ์ทั้งหมด
    assets_list = AssetItem.objects.select_related('asset_code', 'subcategory__category', 'storage_location').all().order_by('id')

    if query:
        assets_list = assets_list.filter(Q(item_name__icontains=query) | Q(asset_code__serial_year__icontains=query))
    
    if category_id:
        assets_list = assets_list.filter(subcategory__category__id=category_id)
        
    if location_id:
        assets_list = assets_list.filter(storage_location__id=location_id)
        
    if status:
        assets_list = assets_list.filter(damage_status=status)

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
        
    categories = AssetCategory.objects.all()
    storage_locations = StorageLocation.objects.all()
    damage_statuses = AssetItem.objects.exclude(damage_status__isnull=True).exclude(damage_status='').values_list('damage_status', flat=True).distinct()
    
    context = {
        'assets': assets,
        'query': query,
        'selected_category': int(category_id) if category_id.isdigit() else '',
        'selected_location': int(location_id) if location_id.isdigit() else '',
        'selected_status': status,
        'categories': categories,
        'storage_locations': storage_locations,
        'damage_statuses': damage_statuses,
        "loan_pending_count": count_pending_asset_loans(),
    }
    
    # ส่งข้อมูล assets ที่ถูกแบ่งหน้าแล้วไปยัง template
    return render(request, 'assets/items/asset_list.html', context)

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

    return render(request, "assets/items/add_asset_item.html", {
        "asset_code_form": asset_code_form,
        "asset_item_form": asset_item_form,
        "categories": categories,
        "loan_pending_count": count_pending_asset_loans(), 
    })


# รายละเอียดครุภัณฑ์
@login_required
def asset_detail(request, pk):
    """ฟังก์ชันสำหรับแสดงรายละเอียดของครุภัณฑ์"""
    asset = get_object_or_404(AssetItem, pk=pk)
    # หากต้องการใช้ฟังก์ชัน calculate_annual_depreciation
    annual_depreciation = asset.calculate_annual_depreciation()
    return render(request, 'assets/items/asset_detail.html', {
        'asset': asset,
        'annual_depreciation': annual_depreciation,
        'loan_pending_count': count_pending_asset_loans(),
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
    
    return render(request, 'assets/items/asset_edit.html', {
        'asset_item_form': asset_item_form,
        'asset_code_form': asset_code_form,
        'asset': asset,
        'categories': categories,
        "loan_pending_count": count_pending_asset_loans(),
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
#     return render(request, 'assets/home/create_asset_ownership.html', {'form': form})

@login_required
def my_assets_view(request):
    """ฟังก์ชันแสดงรายการครุภัณฑ์ที่ผู้ใช้งานครอบครองอยู่ปัจจุบัน"""
    from django.db.models import Exists, OuterRef
    from assets.models import AssetTransferItem

    query = request.GET.get('q', '')
    
    pending_items = AssetTransferItem.objects.filter(
        asset=OuterRef('asset'),
        request_form__status__in=['PENDING_HEAD', 'PENDING_DIRECTOR', 'PENDING_ACTION']
    )
    
    my_ownerships = AssetOwnership.objects.filter(user=request.user, is_active=True).select_related('asset').annotate(
        has_pending_request=Exists(pending_items)
    )
    
    if query:
        my_ownerships = my_ownerships.filter(
            Q(asset__item_name__icontains=query) |
            Q(asset__asset_code__asset_type__icontains=query) |
            Q(asset__asset_code__asset_kind__icontains=query) |
            Q(asset__asset_code__asset_character__icontains=query) |
            Q(asset__asset_code__serial_year__icontains=query)
        )
    
    context = {
        'my_ownerships': my_ownerships,
        'query': query,
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, 'assets/ownership/my_assets.html', context)

# @login_required
# def create_request_view(request):
#     """ฟังก์ชันสำหรับให้ผู้ใช้งานสร้างใบคำร้องขอเคลื่อนย้าย/ส่งคืน"""
#     my_active_assets = AssetOwnership.objects.filter(user=request.user, is_active=True)
#     all_locations = StorageLocation.objects.all()

#     if request.method == 'POST':
#         # รับค่าจากฟอร์ม HTML
#         asset_id = request.POST.get('asset_id')
#         action_type = request.POST.get('action_type')
#         condition = request.POST.get('condition')
#         transfer_to_id = request.POST.get('transfer_to_location')
#         remark = request.POST.get('remark')

#         asset = get_object_or_404(AssetItem, id=asset_id)
#         transfer_to_location = StorageLocation.objects.filter(id=transfer_to_id).first() if transfer_to_id else None

#         # 1. สร้างหัวใบคำร้อง
#         new_request = AssetTransferRequest.objects.create(
#             requester=request.user,
#             department_name=request.user.department if hasattr(request.user, 'department') else "ไม่ระบุ",
#             status='PENDING_HEAD'
#         )

#         # 2. สร้างรายการครุภัณฑ์ในใบคำร้อง
#         AssetTransferItem.objects.create(
#             request_form=new_request,
#             asset=asset,
#             action_type=action_type,
#             condition=condition,
#             transfer_from_location=asset.storage_location,
#             transfer_to_location=transfer_to_location,
#             remark=remark
#         )

#         messages.success(request, 'สร้างใบคำร้องสำเร็จ ระบบกำลังส่งเรื่องให้หัวหน้างาน')
#         return redirect('my_assets')

#     context = {
#         'my_assets': [own.asset for own in my_active_assets],
#         'locations': all_locations
#     }
#     return render(request, 'assets/ownership/create_request.html', context)

# @login_required
# def create_request_view(request):
#     """ฟังก์ชันสำหรับให้ผู้ใช้งานสร้างใบคำร้องขอเคลื่อนย้าย/ส่งคืน"""
#     my_active_assets = AssetOwnership.objects.filter(user=request.user, is_active=True)
#     all_locations = StorageLocation.objects.all()

#     if request.method == 'POST':
#         # ✅ 1. เปลี่ยนมารับค่า asset_ids เป็นลิสต์ (Array) ด้วย getlist()
#         asset_ids = request.POST.getlist('asset_ids') 
#         action_type = request.POST.get('action_type')
#         condition = request.POST.get('condition')
#         transfer_to_id = request.POST.get('transfer_to_location')
#         remark = request.POST.get('remark')

#         transfer_to_location = StorageLocation.objects.filter(id=transfer_to_id).first() if transfer_to_id else None

#         # ตรวจสอบว่ามีการเลือกครุภัณฑ์มาหรือไม่
#         if not asset_ids:
#             messages.error(request, 'กรุณาเลือกครุภัณฑ์อย่างน้อย 1 รายการ')
#             return redirect('assets:create_request')

#         # ✅ 2. สร้างหัวใบคำร้องแค่ 1 ใบ
#         new_request = AssetTransferRequest.objects.create(
#             requester=request.user,
#             department_name=request.user.department if hasattr(request.user, 'department') else "ไม่ระบุ",
#             status='PENDING_HEAD'
#         )

#         # ✅ 3. วนลูปเพื่อนำครุภัณฑ์ทุกชิ้นที่เลือก ไปใส่ในใบคำร้องนี้
#         for asset_id in asset_ids:
#             asset = get_object_or_404(AssetItem, id=asset_id)
#             AssetTransferItem.objects.create(
#                 request_form=new_request,
#                 asset=asset,
#                 action_type=action_type,
#                 condition=condition,
#                 transfer_from_location=asset.storage_location,
#                 transfer_to_location=transfer_to_location,
#                 remark=remark
#             )

#         messages.success(request, f'สร้างใบคำร้องสำหรับครุภัณฑ์ {len(asset_ids)} รายการสำเร็จ ระบบกำลังส่งเรื่องให้หัวหน้างาน')
#         return redirect('assets:my_assets') # ปรับ URL ให้ตรงกับของคุณ

#     context = {
#         'my_assets': [own.asset for own in my_active_assets],
#         'locations': all_locations
#     }
#     return render(request, 'assets/ownership/create_request.html', context)

@login_required
def create_request_view(request):
    """ฟังก์ชันสร้างใบคำร้อง (อัปเดตดึง 'กลุ่มงาน' จาก Profile)"""
    from django.db.models import Exists, OuterRef
    from assets.models import AssetTransferItem

    pending_items = AssetTransferItem.objects.filter(
        asset=OuterRef('asset'),
        request_form__status__in=['PENDING_HEAD', 'PENDING_DIRECTOR', 'PENDING_ACTION']
    )
    my_active_assets = AssetOwnership.objects.filter(user=request.user, is_active=True).annotate(
        has_pending_request=Exists(pending_items)
    )
    
    all_locations = StorageLocation.objects.all()

    if request.method == 'POST':
        asset_ids = request.POST.getlist('asset_ids') 
        action_type = request.POST.get('action_type')
        condition = request.POST.get('condition')
        transfer_to_id = request.POST.get('transfer_to_location')
        remark = request.POST.get('remark')

        transfer_to_location = StorageLocation.objects.filter(id=transfer_to_id).first() if transfer_to_id else None

        if not asset_ids:
            messages.error(request, 'กรุณาเลือกครุภัณฑ์อย่างน้อย 1 รายการ')
            return redirect('assets:create_request')

        # ✅ แก้ไขตรงนี้: ดึงชื่อกลุ่ม/ฝ่ายจากโมเดล Profile โดยใช้ str() 
        try:
            department_name = str(request.user.profile.workgroup)
        except Exception as e:
            print("เกิดข้อผิดพลาดในการดึงกลุ่มงาน:", e) # จะแสดงใน Terminal ถ้ามี Error
            department_name = "ไม่ระบุ"

        new_request = AssetTransferRequest.objects.create(
            requester=request.user,
            department_name=department_name,
            status='PENDING_HEAD'
        )

        for asset_id in asset_ids:
            asset = get_object_or_404(AssetItem, id=asset_id)
            AssetTransferItem.objects.create(
                request_form=new_request,
                asset=asset,
                action_type=action_type,
                condition=condition,
                transfer_from_location=asset.storage_location,
                transfer_to_location=transfer_to_location,
                remark=remark
            )

        messages.success(request, f'สร้างใบคำร้องจำนวน {len(asset_ids)} รายการสำเร็จ ระบบกำลังส่งเรื่องให้หัวหน้างาน')
        return redirect('assets:transfer_request_list') 

    my_assets_list = []
    for own in my_active_assets:
        asset = own.asset
        asset.has_pending_request = own.has_pending_request
        my_assets_list.append(asset)

    context = {
        'my_assets': my_assets_list,
        'locations': all_locations,
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, 'assets/ownership/create_request.html', context)


@login_required
def transfer_request_list_view(request):
    """ฟังก์ชันแสดงหน้ารวมคำร้อง (แยกสิทธิ์การมองเห็น)"""
    my_requests = AssetTransferRequest.objects.filter(requester=request.user).order_by('-id')

    all_requests = None
    # ✅ ตรวจสอบสิทธิ์ว่ามีสิทธิ์เป็น แอดมิน/ผู้จัดการ/พัสดุ/ผู้บริหาร หรือไม่ ถ้ามีให้เห็นรายการรออนุมัติ
    if request.user.is_admin or request.user.is_manager or request.user.is_warehouse_manager or request.user.is_executive:
        all_requests = AssetTransferRequest.objects.all().order_by('-id')

    context = {
        'my_requests': my_requests,
        'all_requests': all_requests,
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, 'assets/ownership/transfer_request_list.html', context)



# @login_required
# def request_detail_view(request, request_id):
#     """หน้าดูรายละเอียดแบบฟอร์ม (และใช้สำหรับสั่งพิมพ์ / อนุมัติ)"""
#     transfer_request = get_object_or_404(AssetTransferRequest, id=request_id)
#     items = transfer_request.request_items.all()

#     # ✅ 1. กำหนดสิทธิ์การมองเห็นปุ่มอนุมัติ ตามโมเดล MyUser ของคุณ
#     can_approve_head = request.user.is_manager or request.user.is_admin
#     can_approve_director = request.user.is_executive or request.user.is_admin
#     can_execute_action = request.user.is_warehouse_manager or request.user.is_admin

#     if request.method == 'POST':
#         # ฟอร์มหัวหน้างาน (ส่วนที่ 2)
#         if 'head_approval' in request.POST and can_approve_head:
#             transfer_request.head_approved = request.POST.get('head_approval') == 'True'
#             transfer_request.head_reject_reason = request.POST.get('head_reject_reason', '')
#             transfer_request.head_approver = request.user
#             transfer_request.head_action_date = timezone.now().date()
#             transfer_request.status = 'PENDING_DIRECTOR' if transfer_request.head_approved else 'REJECTED'
#             transfer_request.save()
#             messages.success(request, 'บันทึกความเห็นหัวหน้างานแล้ว')

#         # ฟอร์มผู้อำนวยการ (ส่วนที่ 3)
#         elif 'director_approval' in request.POST and can_approve_director:
#             transfer_request.director_approved = request.POST.get('director_approval') == 'True'
#             transfer_request.director_reject_reason = request.POST.get('director_reject_reason', '')
#             transfer_request.director_approver = request.user
#             transfer_request.director_action_date = timezone.now().date()
#             transfer_request.status = 'PENDING_ACTION' if transfer_request.director_approved else 'REJECTED'
#             transfer_request.save()
#             messages.success(request, 'บันทึกการอนุมัติของผู้อำนวยการแล้ว')
            
#         # ฟอร์มเจ้าหน้าที่พัสดุ (ส่วนที่ 4)
#         elif 'officer_action_status' in request.POST and can_execute_action:
#             action_status = request.POST.get('officer_action_status')
#             transfer_request.officer_action_status = action_status
#             transfer_request.officer_fail_reason = request.POST.get('fail_reason', '')
#             transfer_request.officer = request.user
#             transfer_request.officer_action_date = timezone.now().date()
            
#             if action_status in ['MOVED', 'RETURNED']:
#                 transfer_request.status = 'COMPLETED'
#                 transfer_request.save()
#                 # เรียกฟังก์ชันตัดยอดที่อยู่ใน models.py
#                 if hasattr(transfer_request, 'apply_ownership_and_location_changes'):
#                     transfer_request.apply_ownership_and_location_changes()
#                 messages.success(request, 'ดำเนินการและอัปเดตข้อมูลครุภัณฑ์สำเร็จ')
#             else:
#                 transfer_request.status = 'REJECTED'
#                 transfer_request.save()
#                 messages.warning(request, 'บันทึกว่าไม่สามารถดำเนินการได้')

#         return redirect('assets:request_detail', request_id=request_id)

#     # ✅ 2. ส่งตัวแปรสิทธิ์เหล่านี้แนบไปกับ Context เพื่อให้ HTML รู้ว่าต้องโชว์ฟอร์มไหน
#     context = {
#         'req': transfer_request,
#         'items': items,
#         'can_approve_head': can_approve_head,
#         'can_approve_director': can_approve_director,
#         'can_execute_action': can_execute_action,
#     }
#     return render(request, 'assets/ownership/request_detail.html', context)



@login_required
def request_detail_view(request, request_id):
    """หน้าดูรายละเอียดแบบฟอร์ม และปุ่มพิจารณาอนุมัติตามระดับสิทธิ์จริงในระบบ"""
    transfer_request = get_object_or_404(AssetTransferRequest, id=request_id)
    items = transfer_request.request_items.all()

    # ตรวจสอบสิทธิ์การใช้งานจากฟิลด์ของโมเดลผู้ใช้งานโดยตรง
    is_super = request.user.is_superuser or getattr(request.user, 'is_admin', False)
    
    # แยกสิทธิ์ให้ตรงตามตารางและเงื่อนไขของแต่ละฝ่าย
    can_approve_head = is_super or getattr(request.user, 'is_manager', False)
    can_approve_director = is_super or getattr(request.user, 'is_executive', False)
    can_execute_action = is_super or getattr(request.user, 'is_warehouse_manager', False)

    # can_approve_head = request.user.is_manager or request.user.is_admin
    # can_approve_director = request.user.is_executive or request.user.is_admin
    # can_execute_action = request.user.is_warehouse_manager or request.user.is_admin

    if request.method == 'POST':
        # 1. ส่วนของหัวหน้างานพัสดุ (ส่วนที่ 2)
        if 'head_approval' in request.POST and can_approve_head:
            transfer_request.head_approved = request.POST.get('head_approval') == 'True'
            transfer_request.head_reject_reason = request.POST.get('head_reject_reason', '')
            transfer_request.head_approver = request.user
            transfer_request.head_action_date = timezone.now().date()
            transfer_request.status = 'PENDING_DIRECTOR' if transfer_request.head_approved else 'REJECTED'
            transfer_request.save()
            messages.success(request, 'บันทึกความเห็นหัวหน้างานแล้ว')

        # 2. ส่วนของผู้อำนวยการ (ส่วนที่ 3)
        elif 'director_approval' in request.POST and can_approve_director:
            transfer_request.director_approved = request.POST.get('director_approval') == 'True'
            transfer_request.director_reject_reason = request.POST.get('director_reject_reason', '')
            transfer_request.director_approver = request.user
            transfer_request.director_action_date = timezone.now().date()
            transfer_request.status = 'PENDING_ACTION' if transfer_request.director_approved else 'REJECTED'
            transfer_request.save()
            messages.success(request, 'บันทึกการอนุมัติของผู้อำนวยการแล้ว')
            
        # 3. ส่วนของเจ้าหน้าที่พัสดุผู้ดำเนินการ (ส่วนที่ 4)
        elif 'officer_action_status' in request.POST and can_execute_action:
            action_status = request.POST.get('officer_action_status')
            transfer_request.officer_action_status = action_status
            transfer_request.officer_fail_reason = request.POST.get('fail_reason', '')
            transfer_request.officer = request.user
            transfer_request.officer_action_date = timezone.now().date()
            
            if action_status in ['MOVED', 'RETURNED']:
                transfer_request.status = 'COMPLETED'
                transfer_request.save()
                # เรียกลอจิกสลับชื่อผู้ครอบครองและสถานที่ตั้งใหม่ในฐานข้อมูลอัตโนมัติ
                if hasattr(transfer_request, 'apply_ownership_and_location_changes'):
                    transfer_request.apply_ownership_and_location_changes()
                messages.success(request, 'ดำเนินการและอัปเดตข้อมูลครุภัณฑ์สำเร็จ')
            else:
                transfer_request.status = 'REJECTED'
                transfer_request.save()
                messages.warning(request, 'บันทึกว่าไม่สามารถดำเนินการได้')

        return redirect('assets:request_detail', request_id=request_id)

    context = {
        'req': transfer_request,
        'items': items,
        'can_approve_head': can_approve_head,
        'can_approve_director': can_approve_director,
        'can_execute_action': can_execute_action,
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, 'assets/ownership/request_detail.html', context)


@login_required
def transfer_request_list_view(request):
    """ฟังก์ชันแสดงหน้ารวมคำร้อง (คำร้องของฉัน)"""
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    # --- 1. คำร้องของฉัน ---
    my_requests = AssetTransferRequest.objects.filter(requester=request.user).order_by('-id')
    if query:
        my_requests = my_requests.filter(
            Q(id__icontains=query) |
            Q(request_items__asset__item_name__icontains=query) |
            Q(request_items__asset__asset_code__serial_year__icontains=query)
        ).distinct()
    if status_filter:
        my_requests = my_requests.filter(status=status_filter)

    # ระบบ Pagination สำหรับ "คำร้องของฉัน"
    my_paginator = Paginator(my_requests, 10)
    my_page_number = request.GET.get('page')
    my_page_obj = my_paginator.get_page(my_page_number)

    context = {
        'my_requests': my_page_obj,
        'query': query,
        'status_filter': status_filter,
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, 'assets/ownership/transfer_request_list.html', context)


@login_required
def admin_transfer_request_list_view(request):
    """ฟังก์ชันแสดงรายการคำร้องขอเคลื่อนย้ายสำหรับเจ้าหน้าที่ (รอพิจารณา)"""
    if not (request.user.is_admin or request.user.is_manager or request.user.is_warehouse_manager or request.user.is_executive):
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('assets:transfer_request_list')

    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    all_requests = AssetTransferRequest.objects.all().order_by('-id')
    
    if query:
        all_requests = all_requests.filter(
            Q(id__icontains=query) |
            Q(requester__first_name__icontains=query) |
            Q(requester__last_name__icontains=query) |
            Q(requester__username__icontains=query) |
            Q(request_items__asset__item_name__icontains=query)
        ).distinct()
    if status_filter:
        all_requests = all_requests.filter(status=status_filter)
    else:
        # Default view might be just pending ones, or all. Let's keep all and allow filtering.
        pass
        
    all_paginator = Paginator(all_requests, 10)
    all_page_number = request.GET.get('page')
    all_page_obj = all_paginator.get_page(all_page_number)

    context = {
        'all_requests': all_page_obj,
        'query': query,
        'status_filter': status_filter,
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, 'assets/ownership/admin_transfer_request_list.html', context)


# @login_required
# def request_detail_view(request, request_id):
#     """หน้าดูรายละเอียดและพิจารณาอนุมัติ (แยกสิทธิ์คนกด)"""
#     transfer_request = get_object_or_404(AssetTransferRequest, id=request_id)
#     items = transfer_request.request_items.all()

#     # เช็คสิทธิ์เพื่อส่งไปเปิด/ปิดฟอร์มในหน้า HTML
#     can_approve_head = request.user.is_manager or request.user.is_admin
#     can_approve_director = request.user.is_executive or request.user.is_admin
#     can_execute_action = request.user.is_warehouse_manager or request.user.is_admin

#     if request.method == 'POST':
#         # 1. ฟอร์มหัวหน้างาน
#         if 'head_approval' in request.POST and can_approve_head:
#             transfer_request.head_approved = request.POST.get('head_approval') == 'True'
#             transfer_request.head_reject_reason = request.POST.get('head_reject_reason', '')
#             transfer_request.head_approver = request.user
#             transfer_request.head_action_date = timezone.now().date()
#             transfer_request.status = 'PENDING_DIRECTOR' if transfer_request.head_approved else 'REJECTED'
#             transfer_request.save()
#             messages.success(request, 'บันทึกความเห็นหัวหน้างานแล้ว')

#         # 2. ฟอร์มผู้อำนวยการ
#         elif 'director_approval' in request.POST and can_approve_director:
#             transfer_request.director_approved = request.POST.get('director_approval') == 'True'
#             transfer_request.director_reject_reason = request.POST.get('director_reject_reason', '')
#             transfer_request.director_approver = request.user
#             transfer_request.director_action_date = timezone.now().date()
#             transfer_request.status = 'PENDING_ACTION' if transfer_request.director_approved else 'REJECTED'
#             transfer_request.save()
#             messages.success(request, 'บันทึกการอนุมัติของผู้อำนวยการแล้ว')
            
#         # 3. ฟอร์มเจ้าหน้าที่พัสดุดำเนินการ (ยุบรวมจากที่เคยแยกหน้า)
#         elif 'officer_action_status' in request.POST and can_execute_action:
#             action_status = request.POST.get('officer_action_status')
#             transfer_request.officer_action_status = action_status
#             transfer_request.officer_fail_reason = request.POST.get('fail_reason', '')
#             transfer_request.officer = request.user
#             transfer_request.officer_action_date = timezone.now().date()
            
#             if action_status in ['MOVED', 'RETURNED']:
#                 transfer_request.status = 'COMPLETED'
#                 transfer_request.save()
#                 transfer_request.apply_ownership_and_location_changes() # ฟังก์ชันอัปเดต DB อัตโนมัติ
#                 messages.success(request, 'ดำเนินการและตัดยอดครุภัณฑ์ในระบบสำเร็จ')
#             else:
#                 transfer_request.status = 'REJECTED'
#                 transfer_request.save()
#                 messages.warning(request, 'บันทึกว่าไม่สามารถดำเนินการได้')

#         return redirect('assets:request_detail', request_id=request_id)

#     context = {
#         'req': transfer_request,
#         'items': items,
#         'can_approve_head': can_approve_head,
#         'can_approve_director': can_approve_director,
#         'can_execute_action': can_execute_action,
#     }
#     return render(request, 'assets/ownership/request_detail.html', context)

# ==========================================
# ฝั่งแอดมิน / เจ้าหน้าที่พัสดุ (Admin)
# ==========================================

# @login_required
# def admin_add_ownership_view(request):
#     """ฟังก์ชันสำหรับแอดมิน/เจ้าหน้าที่ บันทึกมอบหมายครุภัณฑ์ให้ผู้ใช้งาน (ยืมใช้/ครอบครอง)"""
#     # ตรวจสอบสิทธิ์แอดมิน
#     if not request.user.is_staff:
#         messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
#         return redirect('my_assets')

#     # ✅ แก้ไขจุดนี้: เรียกจากคลังคลาส MyUser ตรงๆ และใช้ .order_by() ให้ถูกต้องตามหลัก Django
#     all_users = MyUser.objects.all().order_by('first_name')
#     all_assets = AssetItem.objects.all() 

#     if request.method == 'POST':
#         user_id = request.POST.get('user_id')
#         asset_id = request.POST.get('asset_id')
#         start_date = request.POST.get('start_date')

#         # ✅ แก้ไขจุดนี้: เปลี่ยนจากอ้างอิง User (ที่เป็น instance เก่า) มาใช้คลาส MyUser
#         target_user = get_object_or_404(MyUser, id=user_id)
#         target_asset = get_object_or_404(AssetItem, id=asset_id)
        
#         if not start_date:
#             start_date = timezone.now().date()

#         # ลอจิกตรวจสอบและเคลียร์ผู้ครอบครองคนเก่าออก
#         AssetOwnership.objects.filter(asset=target_asset, is_active=True).update(
#             is_active=False,
#             end_date=start_date
#         )

#         # บันทึกผู้ครอบครองปัจจุบันคนใหม่เข้าไป
#         AssetOwnership.objects.create(
#             asset=target_asset,
#             user=target_user,
#             start_date=start_date,
#             is_active=True 
#         )

#         messages.success(request, f'บันทึกการมอบครุภัณฑ์ให้คุณ {target_user.first_name} {target_user.last_name} เรียบร้อยแล้ว')
#         return redirect('admin_ownership_list') 

#     context = {
#         'users': all_users,
#         'assets': all_assets,
#     }
#     return render(request, 'assets/ownership/admin_add_ownership.html', context)

@login_required
def admin_add_ownership_view(request):
    """ฟังก์ชันสำหรับแอดมิน/เจ้าหน้าที่ บันทึกมอบหมายครุภัณฑ์ให้ผู้ใช้งาน (ยืมใช้/ครอบครอง)"""
    if not request.user.is_staff:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('my_assets')

    all_users = MyUser.objects.all().order_by('first_name')
    all_assets = AssetItem.objects.all() 

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        # ✅ ใช้ getlist() เพื่อรับค่าเป็น Array รองรับการเลือกหลายรายการ
        asset_ids = request.POST.getlist('asset_ids') 
        start_date = request.POST.get('start_date')

        target_user = get_object_or_404(MyUser, id=user_id)
        
        if not start_date:
            start_date = timezone.now().date()

        # ตรวจสอบว่ามีการเลือกครุภัณฑ์มาหรือไม่
        if not asset_ids:
            messages.error(request, 'กรุณาเลือกครุภัณฑ์อย่างน้อย 1 รายการ')
            return redirect('admin_add_ownership')

        # ✅ วนลูปบันทึกครุภัณฑ์ทุกชิ้นที่ถูกเลือก
        for asset_id in asset_ids:
            target_asset = get_object_or_404(AssetItem, id=asset_id)
            
            # ลอจิกตรวจสอบและเคลียร์ผู้ครอบครองคนเก่าออก (ทำทีละชิ้น)
            AssetOwnership.objects.filter(asset=target_asset, is_active=True).update(
                is_active=False,
                end_date=start_date
            )

            # บันทึกผู้ครอบครองปัจจุบันคนใหม่เข้าไป
            AssetOwnership.objects.create(
                asset=target_asset,
                user=target_user,
                start_date=start_date,
                is_active=True 
            )

        messages.success(request, f'บันทึกการมอบครุภัณฑ์จำนวน {len(asset_ids)} รายการ ให้คุณ {target_user.first_name} {target_user.last_name} เรียบร้อยแล้ว')
        # เปลี่ยนชื่อ URL ตรงนี้ให้ตรงกับใน urls.py ของคุณ
        return redirect('assets:admin_ownership_list') 

    context = {
        'users': all_users,
        'assets': all_assets,
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, 'assets/ownership/admin_add_ownership.html', context)

@login_required
def admin_ownership_list_view(request):
    """ฟังก์ชันแสดงรายการผู้ครอบครองครุภัณฑ์ทั้งหมดในระบบ (สำหรับแอดมิน)"""
    # ตรวจสอบสิทธิ์เบื้องต้น (สมมติว่าเช็คจาก is_staff)
    if not request.user.is_staff:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('my_assets')

    query = request.GET.get('q', '').strip()
    all_active_ownerships = AssetOwnership.objects.all().select_related('user', 'asset', 'asset__asset_code')
    
    if query:
        all_active_ownerships = all_active_ownerships.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query) |
            Q(asset__item_name__icontains=query) |
            Q(asset__asset_code__serial_year__icontains=query)
        )
        
    # ระบบ Pagination
    paginator = Paginator(all_active_ownerships, 20) # แสดง 20 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'ownerships': page_obj,
        'query': query,
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, 'assets/ownership/admin_ownership_list.html', context)

@login_required
def admin_complete_request_view(request, request_id):
    """ฟังก์ชันสำหรับเจ้าหน้าที่พัสดุกดดำเนินการเสร็จสิ้น (ส่วนที่ 4)"""
    if not request.user.is_staff:
        return redirect('my_assets')

    transfer_request = get_object_or_404(AssetTransferRequest, id=request_id)

    if request.method == 'POST':
        action_status = request.POST.get('action_status') # MOVED, RETURNED, FAILED
        fail_reason = request.POST.get('fail_reason', '')

        # อัปเดตข้อมูลส่วนที่ 4
        transfer_request.officer_action_status = action_status
        transfer_request.officer_fail_reason = fail_reason
        transfer_request.officer = request.user
        transfer_request.officer_action_date = timezone.now().date()
        
        if action_status in ['MOVED', 'RETURNED']:
            transfer_request.status = 'COMPLETED'
            transfer_request.save()
            # เรียกใช้ฟังก์ชันอัปเดตผู้ครอบครองและสถานที่อัตโนมัติ ที่เราเขียนไว้ใน Models
            transfer_request.apply_ownership_and_location_changes()
            messages.success(request, 'ดำเนินการและอัปเดตข้อมูลครุภัณฑ์สำเร็จ')
        else:
            transfer_request.status = 'REJECTED'
            transfer_request.save()
            messages.warning(request, 'บันทึกว่าไม่สามารถดำเนินการได้')

        return redirect('admin_ownership_list') # หรือกลับไปหน้าจัดการคำร้อง

    return render(request, 'assets/ownership/admin_complete_request.html', {'transfer_request': transfer_request,"loan_pending_count": count_pending_asset_loans(),},)


# -----------------------------------------------------------------------------------------------------------------------------------------------



# บันทึกการตรวจเช็คครุภัณฑ์
@login_required
def check_asset(request, asset_id):
    setting, _ = AssetSystemSetting.objects.get_or_create(id=1)
    if not request.user.is_staff and not request.user.is_superuser:
        if not setting.is_public_check_enabled or not setting.allowed_users.filter(id=request.user.id).exists():
            messages.warning(request, "ขณะนี้ระบบยังไม่เปิดให้บุคคลทั่วไปทำการตรวจนับครุภัณฑ์")
            return redirect('assets:home_assets')

    # ดึงข้อมูลครุภัณฑ์ที่ต้องการตรวจเช็ค
    asset = get_object_or_404(AssetItem, id=asset_id)
    storage_locations = StorageLocation.objects.all()  # ดึงสถานที่เก็บทั้งหมด

    if request.method == "POST":
        # ตรวจสอบว่ามีการตรวจนับในปีงบประมาณนี้ไปแล้วหรือไม่
        fiscal_year = request.POST.get("fiscal_year")
        existing_check = AssetCheck.objects.filter(asset=asset, fiscal_year=fiscal_year).first()
        
        if existing_check:
            messages.error(request, f'❌ ไม่สามารถบันทึกได้! ครุภัณฑ์ "{asset.item_name}" ได้รับการตรวจนับในปีงบประมาณ {fiscal_year} ไปแล้ว')
            return redirect('assets:asset_detail', pk=asset.id)
            
        form = AssetCheckForm(request.POST, request.FILES, asset=asset)

        if form.is_valid():
            check = form.save(commit=False, user=request.user)
            check.status = True # ถือว่ากดบันทึกคือตรวจแล้ว
            check.save()
            
            # อัปเดตสถานที่เก็บ
            asset.storage_location_id = request.POST.get("storage_location")
            asset.save()
            
            messages.success(request, f'✅ บันทึกการตรวจนับ "{asset.item_name}" เรียบร้อยแล้ว')
            return redirect('assets:asset_detail', pk=asset.id)
    else:
        # หากเข้ามาหน้าฟอร์ม ให้เช็คก่อนว่าปีนี้ตรวจไปหรือยัง (สมมติปีปัจจุบัน)
        import datetime
        current_year_th = str(datetime.datetime.now().year + 543)
        existing_check = AssetCheck.objects.filter(asset=asset, fiscal_year=current_year_th).first()
        
        if existing_check:
            messages.warning(request, f'⚠️ ครุภัณฑ์ "{asset.item_name}" ได้รับการตรวจนับในปีงบประมาณ {current_year_th} ไปแล้ว หากต้องการตรวจนับสำหรับปีถัดไป กรุณาเปลี่ยนช่อง "ปีงบประมาณ"')
            
        form = AssetCheckForm(asset=asset)

    return render(request, "assets/items/asset_check_form.html", {"form": form, "asset": asset, "storage_locations": storage_locations, "loan_pending_count": count_pending_asset_loans(),})

@login_required
def asset_check_list(request):
    """
    ฟังก์ชันสำหรับแสดงรายการประวัติการตรวจนับครุภัณฑ์
    """
    setting, _ = AssetSystemSetting.objects.get_or_create(id=1)
    if not request.user.is_staff and not request.user.is_superuser:
        if not setting.is_public_check_enabled or not setting.allowed_users.filter(id=request.user.id).exists():
            messages.warning(request, "ขณะนี้ระบบยังไม่เปิดให้บุคคลทั่วไปทำการตรวจนับครุภัณฑ์")
            return redirect('assets:home_assets')

    checks = AssetCheck.objects.all().order_by('-id')
    
    # การค้นหา
    query = request.GET.get('q', '')
    if query:
        checks = checks.filter(
            Q(asset__item_name__icontains=query) |
            Q(asset__asset_code__serial_year__icontains=query)
        )
        
    # กรองตามปีงบประมาณ
    fiscal_year = request.GET.get('fiscal_year', '')
    if fiscal_year:
        checks = checks.filter(fiscal_year=fiscal_year)
        
    # กรองตามสถานะการใช้งาน (ชำรุด, เสื่อมสภาพ, ใช้งานได้)
    damage_status = request.GET.get('damage_status', '')
    if damage_status:
        checks = checks.filter(asset__damage_status=damage_status)

    paginator = Paginator(checks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # รายการปีงบประมาณที่เคยมีการตรวจนับ เพื่อให้เลือกใน dropdown ได้ง่ายๆ
    available_years = AssetCheck.objects.values_list('fiscal_year', flat=True).distinct().order_by('-fiscal_year')

    # === สถิติการตรวจนับ ===
    total_assets_count = AssetItem.objects.count()
    
    # ถ้ามีการเลือกปีงบ ให้ใช้ปีที่เลือก ไม่งั้นใช้ปีงบล่าสุดที่มีข้อมูล
    if fiscal_year:
        selected_year = int(fiscal_year)
    elif available_years.exists():
        selected_year = available_years.first()
    else:
        selected_year = None
    
    if selected_year and total_assets_count > 0:
        checked_count = AssetCheck.objects.filter(fiscal_year=selected_year).values('asset').distinct().count()
        check_percentage = round((checked_count / total_assets_count) * 100, 1)
        unchecked_count = total_assets_count - checked_count
    else:
        checked_count = 0
        check_percentage = 0
        unchecked_count = total_assets_count

    setting, created = AssetSystemSetting.objects.get_or_create(id=1)
    
    context = {
        'checks': page_obj,
        'query': query,
        'fiscal_year_filter': fiscal_year,
        'damage_status_filter': damage_status,
        'available_years': available_years,
        'DAMAGE_STATUS_CHOICES': AssetItem.DAMAGE_STATUS_CHOICES,
        'loan_pending_count': count_pending_asset_loans(),
        'total_assets_count': total_assets_count,
        'checked_count': checked_count,
        'unchecked_count': unchecked_count,
        'check_percentage': check_percentage,
        'selected_year': selected_year,
        'system_setting': setting,
    }
    return render(request, 'assets/items/asset_check_list.html', context)

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
    
    return render(request, 'assets/loans/add_asset_item_loan.html', 
                  {'form': form,
                  "categories": categories,
                  "loan_pending_count": count_pending_asset_loans(),
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
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, 'assets/loans/edit_asset_item_loan.html', context)


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
    context = {
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, "assets/home/calendar.html" , context)



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
                "loan_pending_count": count_pending_asset_loans(),
            }
        })

    return JsonResponse(events, safe=False)

# ------------------------------
# แสดงรายการครุภัณฑ์ สำหรับยืม
# ------------------------------
# @login_required
# def loan_list(request):
#     # เริ่มต้นด้วยการ query ครุภัณฑ์ทั้งหมด
#     asset_items_query = AssetItemLoan.objects.all()
    
#     has_line_account = False
#     if request.user.is_authenticated:
#         # UserLine_Asset.objects.filter(user=request.user).exists()
#         # หรือใช้ try: request.user.userline_asset
        
#         # สมมติว่าคุณต้องการให้แต่ละ MyUser มี UserLine_Asset ได้หลายรายการ
#         # ถ้าต้องการแค่รายการเดียว (ควรใช้ OneToOneField แทน) สามารถใช้ try-except ได้
        
#         # วิธีที่แนะนำสำหรับ ForeignKey:
#         has_line_account = UserLine_Asset.objects.filter(user=request.user).exists()

#     # Prefetch ข้อมูลการจองล่าสุด
#     asset_items_query = asset_items_query.prefetch_related(
#         Prefetch('assetreservation_set',
#                  queryset=AssetReservation.objects.order_by('reserved_date'),
#                  to_attr='current_reservation')
#     )
    
#     query = request.GET.get("q", "")
#     category_id = request.GET.get("category")
#     subcategory_id = request.GET.get("subcategory")
    
#     if query:
#         asset_items_query = asset_items_query.filter(
#             Q(item_name__icontains=query) |
#             Q(asset_code__icontains=query)
#         )

#     selected_category = None
#     if category_id:
#         selected_category = get_object_or_404(AssetCategory, id=category_id)
#         asset_items_query = asset_items_query.filter(subcategory__category=selected_category)

#     selected_subcategory = None
#     if subcategory_id:
#         selected_subcategory = get_object_or_404(Subcategory, id=subcategory_id)
#         asset_items_query = asset_items_query.filter(subcategory=selected_subcategory)
        
#     asset_items = asset_items_query.all()

#     context = {
#         "asset_items": asset_items,
#         "categories": AssetCategory.objects.all(),
#         "subcategories": Subcategory.objects.all(),
#         "selected_category": selected_category,
#         "selected_subcategory": selected_subcategory,
#         "query": query,
#         'has_line_account': has_line_account,
#         "loan_pending_count": count_pending_asset_loans(),
#     }
#     return render(request, "assets/loans/loan_list.html", context)


@login_required
def loan_list(request):
    # สถานะที่ถือว่าเป็นการยืมที่มีผลอยู่ (Active Loans)
    ACTIVE_LOAN_STATUS = ['pending', 'approved', 'overdue', 'returned_pending']
    
    # 1. เริ่มต้นด้วยการ query ครุภัณฑ์ทั้งหมด
    asset_items_query = AssetItemLoan.objects.all()
    
    has_line_account = False
    if request.user.is_authenticated:
        # ตรวจสอบว่าผู้ใช้มีบัญชี LINE ที่ผูกไว้หรือไม่
        has_line_account = UserLine_Asset.objects.filter(user=request.user).exists()

    # 2. **Prefetch ข้อมูลรายการยืมที่กำลังมีผล (Active Loans) และตัดการ Prefetch การจองออก**
    
    # สร้าง Prefetch Object สำหรับ Active Loans
    active_loans_prefetch = Prefetch(
        'issued_loans', # ใช้ related_name จาก IssuingAssetLoan.order_asset
        queryset=IssuingAssetLoan.objects.filter(
            order_asset__status__in=ACTIVE_LOAN_STATUS
        ).select_related('order_asset', 'order_asset__user')
         .order_by('order_asset__date_due'), # เรียงตามกำหนดคืน
        to_attr='active_loan_list' # ชื่อฟิลด์ใหม่สำหรับเก็บ QuerySet ที่ Active
    )
    asset_items_query = asset_items_query.prefetch_related(active_loans_prefetch)
    
    
    # 3. การกรองและค้นหา (Logic เดิม)
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
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, "assets/loans/loan_list.html", context)


# ------------------------------
# แสดงตะกร้า
# ------------------------------
@login_required
def loan_cart(request):
    asset_items = AssetItemLoan.objects.filter(status_borrowing=True)

    context = {
        "asset_items": asset_items,
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, "assets/loans/loan_cart.html", context)


# ------------------------------
# แสดงรายละเอียดครุภัณฑ์
# ------------------------------
@login_required
def loan_detail_view(request, loan_id):
    loan = get_object_or_404(OrderAssetLoan, pk=loan_id)
    context = {
        'loan': loan,
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, 'assets/loans/loan_detail.html', context)



# ------------------------------
# ฟังก์ยืมครุภัณฑ์
# ------------------------------
# @login_required
# def confirm_loan(request):
#     if request.method == "POST":
#         # ✅ ดึง asset_ids จาก form (กัน error ถ้าไม่มีค่า)
#         asset_ids_str = request.POST.get("asset_ids", "").strip()
#         asset_ids = [int(i) for i in asset_ids_str.split(",") if i.isdigit()]

#         # ✅ ดึง assets ที่เลือกมา
#         assets_in_cart = AssetItemLoan.objects.filter(id__in=asset_ids)

#         if not assets_in_cart.exists():
#             messages.error(request, "ไม่มีครุภัณฑ์ในตะกร้า")
#             return redirect("assets:loan_list")

#         # ✅ ใช้ฟอร์มตรวจสอบข้อมูล
#         form = LoanForm(request.POST)
#         if form.is_valid():
#             order = form.save(commit=False)
#             order.user = request.user
#             order.status = "pending"
#             order.save()

#             # ✅ สร้างความสัมพันธ์กับครุภัณฑ์
#             for asset in assets_in_cart:
#                 IssuingAssetLoan.objects.create(order_asset=order, asset=asset)
#                 asset.status_assetloan = True
#                 asset.save(update_fields=["status_assetloan"])  # save เฉพาะ field ที่เปลี่ยน

#             # 🔔 แจ้งเตือนผ่าน LINE
#             try:
#                 notify_admin_assetloan(request, order.id)
#             except Exception as e:
#                 messages.warning(request, f"บันทึกสำเร็จ แต่ส่ง LINE ไม่ได้: {e}")

#             messages.success(request, "ส่งคำขอยืมครุภัณฑ์เรียบร้อย")
#             return redirect("assets:loan_list")
#         else:
#             # ✅ Debug form errors (กันงง)
#             messages.error(request, f"ฟอร์มไม่ถูกต้อง: {form.errors.as_json()}")

#     # ถ้าไม่ใช่ POST กลับหน้าเดิม
#     return redirect("assets:loan_list")


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
            # --- โค้ดที่ต้องเพิ่ม: ตรวจสอบการยืมซ้ำซ้อน ---
            date_of_use = form.cleaned_data['date_of_use'] # วันที่ใช้ (เริ่มยืม)
            date_due = form.cleaned_data['date_due']       # กำหนดคืน (สิ้นสุดการยืม)
            
            # สถานะที่ 'ยัง' ถือว่าเป็นการยืมหรือกำลังจะยืม (ไม่รวมสถานะยกเลิก, ปฏิเสธ, คืนแล้ว)
            ACTIVE_LOAN_STATUS = ['pending', 'approved', 'borrowed', 'overdue', 'returned_pending']

            # ตรวจสอบว่าครุภัณฑ์ที่เลือกมีการถูกยืมในช่วงเวลาซ้ำซ้อนหรือไม่
            conflicting_issues = IssuingAssetLoan.objects.filter(
                asset__in=assets_in_cart, # ครุภัณฑ์ที่อยู่ในตะกร้า
                order_asset__status__in=ACTIVE_LOAN_STATUS, # สถานะที่ถือว่ากำลังถูกยืม
                
                # ตรวจสอบช่วงเวลาซ้ำซ้อน (Overlap check)
                order_asset__date_of_use__lt=date_due,
                order_asset__date_due__gt=date_of_use
            ).select_related('asset', 'order_asset').first() # .first() เพื่อเอาแค่รายการแรกที่ชน

            if conflicting_issues:
                asset_name = conflicting_issues.asset.item_name
                order_id = conflicting_issues.order_asset.id
                messages.error(
                    request, 
                    f"ไม่สามารถยืมได้: ครุภัณฑ์ **'{asset_name}'** ถูกจอง/ยืมในออเดอร์ #{order_id} ในช่วงเวลาที่เลือกแล้ว"
                )
                return redirect("assets:loan_list")
            # --- จบโค้ดตรวจสอบการยืมซ้ำซ้อน ---

            order = form.save(commit=False)
            order.user = request.user
            order.status = "pending"
            order.save()

            # ✅ สร้างความสัมพันธ์กับครุภัณฑ์
            for asset in assets_in_cart:
                IssuingAssetLoan.objects.create(order_asset=order, asset=asset)
                asset.status_assetloan = True
                asset.save(update_fields=["status_assetloan"]) # save เฉพาะ field ที่เปลี่ยน

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
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, "assets/loans/reserve_modal.html", context)

# ------------------------------
# ฟังก์ชันแยกที่คำนวณจำนวนรายการที่รออนุมัติ
# ------------------------------
def count_pending_asset_loans():
    """
    นับจำนวนออเดอร์ยืมครุภัณฑ์ที่รอการอนุมัติ (รวมรออนุมัติยืมและรออนุมัติคืน)
    """
    
    # ใช้ Q object ตามที่คุณกำหนด
    return OrderAssetLoan.objects.filter(
        Q(status='pending') | Q(status='overdue') | Q(status='returned_pending')
    ).count()

# ------------------------------
# ฟังก์อนุมัติคืน หน้าออเดอร์เจ้าหน้าที่
# ------------------------------
@login_required
def loan_approval_list(request):
    # ==========================================================
    # 1. ระบบตรวจสอบ อัปเดตสถานะ 'เกินกำหนด' และส่ง Line Notify อัตโนมัติ
    # ==========================================================
    overdue_orders = OrderAssetLoan.objects.filter(
        status__in=['pending', 'approved', 'borrowed'],
        date_due__lt=timezone.now()
    )
    
    if overdue_orders.exists():
        # วนลูปส่งแจ้งเตือนทีละรายการก่อนเปลี่ยนสถานะ
        for loan in overdue_orders:
            # ใช้ฟังก์ชัน notify_borrower ที่คุณมีอยู่แล้ว แต่ส่ง action_type เป็น 'overdue'
            # notify_borrower(loan, action_type="overdue")
            notify_overdue_asset_loan(loan)
            messages.success(request, f"ส่งแจ้งเตือนเกินกำหนดสำหรับ Order #{loan.id} ไปยังผู้ยืม ({loan.user.get_full_name()}) แล้ว")

        # เมื่อส่งแจ้งเตือนครบแล้ว ค่อยเปลี่ยนสถานะในฐานข้อมูลเป็น overdue รวดเดียว
        overdue_orders.update(status='overdue')
    # ==========================================================
    month = request.GET.get('month', timezone.now().month)
    year = request.GET.get('year', timezone.now().year)

    # เพิ่มการรับค่าการค้นหา 'q'
    query = request.GET.get('q', '')

    # รับค่าจาก checkbox 'show_rejected' (จะส่งค่า 'on' ถ้าถูกเลือก)
    # ถ้าไม่มีค่าใน GET จะถือว่าเป็น False (ซ่อนรายการที่ปฏิเสธ/ยกเลิก)
    show_rejected = request.GET.get('show_rejected')

    # เริ่มต้น QuerySet (รายการของเดือน/ปี ที่เลือก + รายการที่ยังไม่คืนจากเดือนก่อนๆ)
    loans = OrderAssetLoan.objects.filter(
        Q(month=month, year=year) |
        Q(status__in=['pending', 'approved', 'borrowed', 'returned_pending', 'overdue'])
    )

    # เพิ่มเงื่อนไขการค้นหา
    if query:
        loans = loans.filter(
            Q(id__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(items__asset__item_name__icontains=query)
            # Q(items__asset__asset_code__icontains=query)
        ).distinct()

    # ************************************************
    # เพิ่มเงื่อนไขการกรองรายการที่ถูกปฏิเสธ/ยกเลิก
    if not show_rejected:
        # ถ้า show_rejected เป็น None (ไม่ได้เลือก Checkbox) ให้ซ่อนรายการเหล่านี้
        loans = loans.exclude(status__in=['rejected', 'cancel'])
    # ************************************************

    loans = loans.order_by('-id')

    months = [(1,'มกราคม'),(2,'กุมภาพันธ์'),(3,'มีนาคม'),(4,'เมษายน'),
              (5,'พฤษภาคม'),(6,'มิถุนายน'),(7,'กรกฎาคม'),(8,'สิงหาคม'),
              (9,'กันยายน'),(10,'ตุลาคม'),(11,'พฤศจิกายน'),(12,'ธันวาคม')]
    years = range(2020, timezone.now().year+2)

    # แปลงเป็น tuple (ปีค.ศ., ปีพ.ศ.) เพื่อใช้แสดงผลใน template
    years_display = [(y, y + 543) for y in years]

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
        # "years": years,
        "years": years_display,  # ✅ ใช้ปี พ.ศ. สำหรับแสดงผล
        "selected_month": int(month),
        "selected_year": int(year),
        "get_params": request.GET.copy(),  # เก็บ GET params สำหรับ pagination
        "query": query,
        "loan_pending_count": count_pending_asset_loans(), 
        "show_rejected": show_rejected is not None, # ส่งค่า Boolean ไปยัง Template

    }
    return render(request, "assets/loans/loan_approval_list.html", context)

# ส่งการแจ้งเตือนเมื่อยืมเกินกำหนด
@login_required
def loan_send_overdue_notification(request, loan_id):
    """
    View สำหรับส่งแจ้งเตือนสถานะเกินกำหนดด้วยตนเอง
    """
    # ตรวจสอบว่าเป็นการ POST เท่านั้น
    if request.method != 'POST':
        return redirect("assets:loan_approval_list")

    try:
        # 🚨 ลองดึง OrderAssetLoan
        loan = OrderAssetLoan.objects.get(pk=loan_id)
    except OrderAssetLoan.DoesNotExist:
        # 🚨 ถ้าหาไม่พบ แทนที่จะโยน 404 ให้ดักจับและแสดงข้อความเตือน
        messages.error(request, f"❌ ไม่พบรายการยืม Order #{loan_id} ในฐานข้อมูล")
        return redirect("assets:loan_approval_list")
        
    if loan.status != 'overdue':
        messages.warning(request, f"Order #{loan.id} มีสถานะเป็น '{loan.get_status_display()}' ไม่ใช่ 'เกินกำหนด' จึงไม่สามารถส่งแจ้งเตือนได้")
        return redirect("assets:loan_approval_list")
        
    # เรียกฟังก์ชันแจ้งเตือนที่ปรับปรุงแล้ว
    notify_borrower(loan, action_type="overdue")
    
    messages.success(request, f"ส่งแจ้งเตือนเกินกำหนดสำหรับ Order #{loan.id} ไปยังผู้ยืม ({loan.user.get_full_name()}) แล้ว")
    return redirect("assets:loan_approval_list")


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
        Q(user=request.user) & (
            Q(month=month, year=year_ad) |
            Q(status__in=['pending', 'approved', 'borrowed', 'returned_pending', 'overdue'])
        )
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
        "loan_pending_count": count_pending_asset_loans(),
    }
    return render(request, 'assets/loans/loan_orders_user.html', context)


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

# ส่งแจ้งเตือนสถานะเกินกำหนดด้วยตนเอง
@login_required
def loan_send_overdue_notification(request, loan_id):
    """
    View สำหรับส่งแจ้งเตือนสถานะเกินกำหนดด้วยตนเอง
    (รับ POST โดยตรงจากปุ่ม)
    """
    if request.method != 'POST':
        messages.warning(request, "ไม่ได้รับคำขอ POST ที่ถูกต้อง")
        return redirect("assets:loan_approval_list")

    try:
        # ตรวจสอบ ID และสถานะ
        loan = get_object_or_404(OrderAssetLoan, pk=loan_id)
    except Exception:
        messages.error(request, f"❌ ไม่พบรายการยืม Order #{loan_id} ในฐานข้อมูล")
        return redirect("assets:loan_approval_list")
        
    if loan.status != 'overdue':
        messages.warning(request, f"Order #{loan.id} มีสถานะเป็น '{loan.get_status_display()}' ไม่ใช่ 'เกินกำหนด' จึงไม่สามารถส่งแจ้งเตือนได้")
        return redirect("assets:loan_approval_list")
        
    # เรียกฟังก์ชันแจ้งเตือน (ฟังก์ชันนี้ไม่ควรมี return redirect)
    notify_overdue_asset_loan(loan)
    
    messages.success(request, f"ส่งแจ้งเตือนเกินกำหนดสำหรับ Order #{loan.id} ไปยังผู้ยืม ({loan.user.get_full_name()}) แล้ว")
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

        # --- ส่วนที่แก้ไข ---
        receiver_position = "" # กำหนดค่าเริ่มต้นเป็นค่าว่าง
        try:
            # ลองเข้าถึง profile และดึงค่า position
            receiver_position = request.user.profile.position
        except Profile.DoesNotExist:
            # ถ้าไม่มี profile ก็จะใช้ค่าว่างที่กำหนดไว้
            pass

        # อัพเดทข้อมูลการคืน
        loan.status = "returned"
        loan.status_return = status_return or "not_damaged"
        loan.received_by = request.user.get_full_name()
        # loan.receiver_position = getattr(request.user, "position", "")
        loan.receiver_position = receiver_position # ใช้ตัวแปรที่ดึงค่ามา
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

    return render(request, 'assets/items/asset_list_cate.html', {
        'categories': categories,
        'form': form,
        'query': query,  # ส่งค่าการค้นหาไปยัง template เพื่อแสดงผล
        "loan_pending_count": count_pending_asset_loans(),
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
    return render(request, 'assets/items/add_category_asset.html', {'form': form})

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

    return render(request, 'assets/items/asset_list_cate.html', {'form': form})

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
        ).order_by('category__name_cate', 'name_sub')
    else:
        # ถ้าไม่มีคำค้นหา ให้ดึงข้อมูลทั้งหมด
        subcategories_list = Subcategory.objects.all().order_by('category__name_cate', 'name_sub')

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

    return render(request, 'assets/items/asset_list_subcate.html', {
        'subcategories': subcategories,
        'categories': categories,
        'form': form,
        'query': query,
        "loan_pending_count": count_pending_asset_loans(),
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
    return render(request, 'assets/items/add_subcategory_asset.html', {'form': form})

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

    return render(request, 'assets/items/asset_list_subcate.html', {'form': form})

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

    return render(request, 'assets/items/asset_list_location.html', {
        'storagelocations': storagelocations,
        'form': form,
        'query': query,  # ส่งค่าการค้นหาไปยัง template เพื่อแสดงผล
        "loan_pending_count": count_pending_asset_loans(),
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

    return render(request, 'assets/items/asset_list_location.html', {'form': form})


# ✅ ลบรายการสถานที่เก็บครุภัณฑ์
def delete_storage_location_asset(request, pk):
    storagelocation = get_object_or_404(StorageLocation, pk=pk)  # ✅ Model ชื่อ StorageLocation
    storagelocation.delete()
    messages.success(request, '🗑 ลบรายการสถานที่เก็บครุภัณฑ์เรียบร้อยแล้ว')
    return redirect('assets:asset_list_storage_location')  # เปลี่ยนชื่อให้ตรงกับ url ที่ใช้งาน

from django.http import JsonResponse
import json
@login_required
def toggle_public_check(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    
    setting, created = AssetSystemSetting.objects.get_or_create(id=1)
    setting.is_public_check_enabled = not setting.is_public_check_enabled
    setting.save()
    
    return JsonResponse({'success': True, 'is_enabled': setting.is_public_check_enabled})

@login_required
def update_allowed_checkers(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_ids = data.get('user_ids', [])
            setting, _ = AssetSystemSetting.objects.get_or_create(id=1)
            setting.allowed_users.set(user_ids)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
            
    # GET method
    setting, _ = AssetSystemSetting.objects.get_or_create(id=1)
    allowed_ids = list(setting.allowed_users.values_list('id', flat=True))
    all_users = MyUser.objects.filter(is_active=True).values('id', 'first_name', 'last_name', 'email')
    return JsonResponse({
        'users': list(all_users),
        'allowed_ids': allowed_ids
    })

from django.http import HttpResponse

@login_required
def download_asset_template(request):
    """
    สร้างไฟล์ Excel Template สำหรับการนำเข้าข้อมูลครุภัณฑ์
    """
    # กำหนดคอลัมน์ตามที่ระบุมา
    columns = [
        'ลำดับ', 'หมวดหมู่หลัก', 'หมวดหมู่ย่อย', 'ชื่อรายการครุภัณฑ์',
        'ประเภท', 'ชนิด', 'ลักษณะ', 'ลำดับ/ปี', 
        'หน่วยนับ', 'ราคาที่ซื้อ', 'วันที่ซื้อ', 'ปีที่ใช้งาน', 
        'อายุการใช้งาน', 'ใช้มาแล้วกี่ปี', 'ค่าความเสื่อมต่อปี', 'ค่าเสื่อมราคาประจำปี (บาท)/วัน',
        'ผู้รับผิดชอบ', 'สถานที่เก็บ', 'ยี่ห้อ/รุ่น', 'หมายเหตุ',
        'สถานะการใช้งาน', 'ยืมได้หรือไม่'
    ]
    
    # ข้อมูลตัวอย่าง
    sample_data = [[
        '1', 'เฟอร์นิเจอร์', 'โต๊ะสำนักงาน', 'โต๊ะทำงานเหล็ก 3 ลิ้นชัก',
        'โต๊ะ', 'โต๊ะทำงาน', 'เหล็ก', '001/67',
        'ตัว', '2500.00', '2024-01-15', '2567',
        '5', '0', '500.00', '1.37',
        'นาย สมชาย', 'ห้องคลัง 1', 'ยี่ห้อ A รุ่น B', 'ใช้งานได้ดี',
        'ใช้งานได้', 'ได้'
    ]]
    
    df = pd.DataFrame(sample_data, columns=columns)
    
    # สร้าง HTTP Response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="asset_import_template.xlsx"'
    
    # ใช้ openpyxl ในการสร้างไฟล์
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
        
    return response
