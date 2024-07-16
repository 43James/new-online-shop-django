from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.core.paginator import Paginator
from app_linebot.views import notify_user_approved
from django.db.models import Q, Sum, Max, F, ExpressionWrapper, DecimalField
from shop.models import Category, MonthlyStockRecord, Product, Stock, Subcategory, Suppliers, Total_Quantity, TotalQuantity, Receiving
from accounts.models import MyUser, Profile, WorkGroup
from orders.models import Order, Issuing
from .forms import AddProductForm, AddCategoryForm, AddSubcategoryForm, EditCategoryForm, EditProductForm, ApproveForm, AddSuppliersForm, EditSubcategoryForm, EditSuppliersForm, EditWorkGroupForm, MonthYearForm, OrderFilterForm,  ReceivingForm, RecordMonthlyStockForm, WorkGroupForm
from django.db.models import F
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime, timedelta
import openpyxl, re
from openpyxl.styles import Alignment
from openpyxl.styles import Font, Border, Side, Alignment
from django.http import HttpResponse
from collections import defaultdict
import calendar
import locale
import plotly.express as px
import pandas as pd
locale.setlocale(locale.LC_TIME, 'th_TH.UTF-8')  # ตั้งค่า locale เป็นภาษาไทย
from .forms import UploadFileForm
from django.http import Http404
from openpyxl import Workbook
from babel.dates import format_datetime
from django.utils.dateparse import parse_date



def thai_month_name(month):
    thai_months = [
        'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน',
        'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม',
        'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
    ]
    return thai_months[month - 1] if 1 <= month <= 12 else ''

def convert_to_buddhist_era(year):
    return year + 543


def count_pending_orders():
    # ดึงข้อมูลออเดอร์ทั้งหมดที่รอการยืนยัน
    pending_orders = Order.objects.filter(status=None)
    return pending_orders.count()


def notify_user_rejected(order_id):
    # ดึงข้อมูลของคำสั่งซื้อ
    order = Order.objects.get(id=order_id)
    
    # สร้างเนื้อหาข้อความอีเมล
    subject = 'การสั่งซื้อของคุณถูกปฏิเสธ'
    html_message = render_to_string('email/order_rejected.html', {'order': order})
    plain_message = strip_tags(html_message)
    from_email = 'your@example.com'  # อีเมลผู้ส่ง
    to_email = order.user.email  # อีเมลผู้รับ
    
    # ส่งอีเมล
    send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)


# def is_general(user):
#     if user.is_general:
#         raise Http404
#     return True

# def is_manager(user):
#     if not user.is_manager:
#         raise Http404
#     return False

# def is_executive(user):
#     if not user.is_executive:
#         raise Http404
#     return False

# def is_admin(user):
#     if not user.is_admin:
#         raise Http404
#     return False

# def is_authorized(user):
#     try:
#         return is_manager(user) and is_executive(user) and is_admin(user)
#     except Http404:
#         return True
    
from django.core.exceptions import PermissionDenied

def is_manager(user):
    if not user.is_manager:
        raise PermissionDenied
    return True

def is_executive(user):
    if not user.is_executive:
        raise PermissionDenied
    return True

def is_admin(user):
    if not user.is_admin:
        raise PermissionDenied
    return True

def is_authorized(user):
    # ถ้าผู้ใช้เป็น is_manager, is_executive หรือ is_admin อย่างใดอย่างหนึ่ง
    if user.is_manager or user.is_executive or user.is_admin:
        return True
    raise PermissionDenied

def is_authorized_manager(user):
    if user.is_manager or user.is_admin:
        return True
    raise PermissionDenied


# นำออกที่สมบูรณ์1
@user_passes_test(is_authorized)
# @login_required
# def export_to_excel(request, month=None, year=None):
#     # Get current datetime
#     now = datetime.now()
    
#     if request.GET.get('month'):
#         month = int(request.GET.get('month'))
#     if request.GET.get('year'):
#         year = int(request.GET.get('year'))
    
#     if not month:
#         month = now.month
#     if not year:
#         year = now.year

#     start_date = datetime(year, month, 1)
#     end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)

#     previous_month_start = (start_date - timedelta(days=1)).replace(day=1)
#     previous_month_end = start_date - timedelta(seconds=1)

#     products = Product.objects.all()

#     report_data = []
#     all_users = set()
#     total_issued_value = Decimal(0)  # ใช้ Decimal แทน float
#     total_issued_value_by_user = defaultdict(Decimal)  # ใช้ Decimal แทน float

#     for product in products:
#         # Calculate previous balance
#         previous_balance = Receiving.objects.filter(
#             product=product, date_created__lte=previous_month_end
#         ).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

#         received_current_month = Receiving.objects.filter(
#             product=product, date_created__range=(start_date, end_date)
#         ).aggregate(total_received=Sum('quantityreceived'))['total_received'] or 0

#         total_balance = previous_balance + received_current_month

#         issued_current_month = Issuing.objects.filter(
#             product=product, datecreated__range=(start_date, end_date), order__status=True
#         ).aggregate(total_issued=Sum('quantity'))['total_issued'] or 0

#         remaining_balance = total_balance - issued_current_month

#         issued_items = Issuing.objects.filter(
#             product=product, datecreated__range=(start_date, end_date), order__status=True
#         )
#         product_total_issued_value = issued_items.aggregate(total_cost=Sum(F('price') * F('quantity')))['total_cost'] or Decimal(0)
#         total_issued_value += product_total_issued_value

#         user_issuings = defaultdict(int)
#         for issuing in issued_items:
#             user_full_name = issuing.order.user.get_first_name()
#             user_issuings[user_full_name] += issuing.quantity
#             all_users.add(user_full_name)
#             total_issued_value_by_user[user_full_name] += issuing.price * issuing.quantity

#         report_data.append({
#             'product': product.product_name,
#             'unit': product.unit,
#             'previous_balance': previous_balance,
#             'total_balance': total_balance,
#             **user_issuings,
#             'issued_current_month': issued_current_month,
#             'remaining_balance': remaining_balance,
#             'total_issued_value': product_total_issued_value,
#             'note': '',
#         })

#     # Create a new Excel workbook and worksheet
#     workbook = openpyxl.Workbook()
#     worksheet = workbook.active

#     # Font styles
#     font_title = Font(name='TH SarabunPSK', size=16, bold=True)
#     font_header = Font(name='TH SarabunPSK', size=14, bold=True)
#     font_data = Font(name='TH SarabunPSK', size=12)
    
#     # Alignment styles
#     align_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
#     # Border styles
#     border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

#     # สร้าง header rows ใน worksheet
#     previous_month_name = thai_month_name(month)
#     previous_year_buddhist = convert_to_buddhist_era(year)
#     header_rows = [
#         ['รายการเบิกวัสดุ'],
#         [f'ประจำเดือน {previous_month_name} พ.ศ. {previous_year_buddhist} ประจำปีงบประมาณ พ.ศ. {previous_year_buddhist}'],
#         ['หน่วยงาน โครงการอุทยานวิทยาศาสตร์ มหาวิทยาลัยอุบลราชธานี']
#     ]
    
#     for idx, header_row in enumerate(header_rows, start=1):
#         worksheet.append(header_row)
#         worksheet.merge_cells(start_row=idx, start_column=1, end_row=idx, end_column=12)
#         cell = worksheet.cell(row=idx, column=1)
#         cell.font = font_title
#         cell.alignment = align_center

#     # สร้าง headers ใน worksheet
#     headers = ['ลำดับ', 'รายการสินค้า', 'หน่วยนับ', 'จำนวนคงเหลือ (ยกมา)', 'รวมจำนวนคงเหลือ'] + list(all_users) + ['รวมจำนวนที่เบิก', 'จำนวนคงเหลือทั้งหมด (หักจากที่เบิก)', 'มูลค่าสินค้าเบิกทั้งสิ้น (บาท)', 'หมายเหตุ']
#     worksheet.append(headers)
    
#     # ตั้งค่ารูปแบบให้กับเซลล์ในหัวข้อ
#     for cell in worksheet[4]:
#         cell.font = font_header
#         cell.alignment = align_center
#         cell.border = border

#     # ลูปเพื่อเพิ่มข้อมูลลงใน worksheet
#     for index, item in enumerate(report_data, start=1):
#         row = [
#             index,
#             item['product'],
#             item['unit'],
#             item['previous_balance'],
#             item['received_current_month'],
#             item['total_balance'],
#             *[item.get(user, 0) for user in sorted(all_users)],
#             item['issued_current_month'],
#             item['remaining_balance'],
#             item['total_issued_value'],
#             item['note']
#         ]
#         worksheet.append(row)

#     # สร้างแถวรวมรายจ่ายที่เบิก
#     total_row = [''] * 4 + ['รวมรายจ่ายที่เบิก'] + [f'{total_issued_value_by_user[user]} บาท' for user in sorted(all_users)] + [''] + [''] + [f'{total_issued_value} บาท'] + ['']
#     worksheet.append(total_row)
    
    
#     # ตั้งค่ารูปแบบให้กับเซลล์ใน worksheet
#     for row in worksheet.iter_rows(min_row=5, max_row=len(report_data) + 5, min_col=1, max_col=len(headers)):
#         for cell in row:
#             cell.font = font_data
#             cell.alignment = align_center
#             cell.border = border

#     # ตั้งค่าความกว้างของคอลัมน์
#     column_dimensions = {
#         'A': 5,
#         'B': 30,
#         'C': 10,
#         'D': 15,
#         'E': 15,
#         'F': 15,
#         'G': 15,
#         'H': 20,
#         'I': 20,
#         'J': 20,
#         'K': 20,
#     }
#     for col, width in column_dimensions.items():
#         worksheet.column_dimensions[col].width = width
    
#     # สร้าง HttpResponse สำหรับไฟล์ Excel และบันทึก workbook ลงใน response
#     response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#     response['Content-Disposition'] = 'attachment; filename=monthly_report_{}_{}.xlsx'.format(month, year)
#     workbook.save(response)
    
#     return response



@login_required
def export_to_excel(request, month=None, year=None):
    # Get current datetime
    now = datetime.now()
    
    if request.GET.get('month'):
        month = int(request.GET.get('month'))
    if request.GET.get('year'):
        year = int(request.GET.get('year'))
    
    if not month:
        month = now.month
    if not year:
        year = now.year

    start_date = datetime(year, month, 1)
    end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)

    previous_month_start = (start_date - timedelta(days=1)).replace(day=1)
    previous_month_end = start_date - timedelta(seconds=1)

    products = Product.objects.all()

    report_data = []
    all_users = set()
    total_issued_value = Decimal(0)  # ใช้ Decimal แทน float
    total_issued_value_by_user = defaultdict(Decimal)  # ใช้ Decimal แทน float

    for product in products:
        # Calculate previous balance
        previous_balance = Receiving.objects.filter(
            product=product, date_created__lte=previous_month_end
        ).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

        received_current_month = Receiving.objects.filter(
            product=product, date_created__range=(start_date, end_date)
        ).aggregate(total_received=Sum('quantityreceived'))['total_received'] or 0

        total_balance = previous_balance + received_current_month

        issued_current_month = Issuing.objects.filter(
            product=product, datecreated__range=(start_date, end_date), order__status=True
        ).aggregate(total_issued=Sum('quantity'))['total_issued'] or 0

        remaining_balance = total_balance - issued_current_month

        issued_items = Issuing.objects.filter(
            product=product, datecreated__range=(start_date, end_date), order__status=True
        )
        product_total_issued_value = issued_items.aggregate(total_cost=Sum(F('price') * F('quantity')))['total_cost'] or Decimal(0)
        total_issued_value += product_total_issued_value

        user_issuings = defaultdict(int)
        for issuing in issued_items:
            user_full_name = issuing.order.user.get_first_name()
            user_issuings[user_full_name] += issuing.quantity
            all_users.add(user_full_name)
            total_issued_value_by_user[user_full_name] += issuing.price * issuing.quantity

        report_data.append({
            'product': product.product_name,
            'unit': product.unit,
            'previous_balance': previous_balance,
            'received_current_month': received_current_month,  # เพิ่มฟิลด์นี้
            'total_balance': total_balance,
            **user_issuings,
            'issued_current_month': issued_current_month,
            'remaining_balance': remaining_balance,
            'total_issued_value': product_total_issued_value,
            'note': '',
        })

    # Create a new Excel workbook and worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    # Font styles
    font_title = Font(name='TH SarabunPSK', size=16, bold=True)
    font_header = Font(name='TH SarabunPSK', size=14, bold=True)
    font_data = Font(name='TH SarabunPSK', size=12)
    
    # Alignment styles
    align_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    # Border styles
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    # สร้าง header rows ใน worksheet
    previous_month_name = thai_month_name(month)
    previous_year_buddhist = convert_to_buddhist_era(year)
    header_rows = [
        ['รายการเบิกวัสดุ'],
        [f'ประจำเดือน {previous_month_name} พ.ศ. {previous_year_buddhist} ประจำปีงบประมาณ พ.ศ. {previous_year_buddhist}'],
        ['หน่วยงาน โครงการอุทยานวิทยาศาสตร์ มหาวิทยาลัยอุบลราชธานี']
    ]
    
    for idx, header_row in enumerate(header_rows, start=1):
        worksheet.append(header_row)
        worksheet.merge_cells(start_row=idx, start_column=1, end_row=idx, end_column=12)
        cell = worksheet.cell(row=idx, column=1)
        cell.font = font_title
        cell.alignment = align_center

    # สร้าง headers ใน worksheet
    headers = ['ลำดับ', 'รายการสินค้า', 'หน่วยนับ', 'จำนวนคงเหลือ (ยกมา)', 'จำนวนรับเข้า (ปัจจุบัน)', 'รวมจำนวนคงเหลือบวกรับเข้า'] + list(all_users) + ['รวมจำนวนที่เบิก', 'จำนวนคงเหลือทั้งหมด (หักจากที่เบิก)', 'มูลค่าสินค้าเบิกทั้งสิ้น (บาท)', 'หมายเหตุ']
    worksheet.append(headers)
    
    # ตั้งค่ารูปแบบให้กับเซลล์ในหัวข้อ
    for cell in worksheet[4]:
        cell.font = font_header
        cell.alignment = align_center
        cell.border = border

    # ลูปเพื่อเพิ่มข้อมูลลงใน worksheet
    for index, item in enumerate(report_data, start=1):
        row = [
            index,
            item['product'],
            item['unit'],
            item['previous_balance'],
            item['received_current_month'],  # เพิ่มฟิลด์นี้
            item['total_balance'],
            *[item.get(user, 0) for user in sorted(all_users)],
            item['issued_current_month'],
            item['remaining_balance'],
            item['total_issued_value'],
            item['note']
        ]
        worksheet.append(row)

    # สร้างแถวรวมรายจ่ายที่เบิก
    total_row = [''] * 5 + ['รวมรายจ่ายที่เบิก'] + [f'{total_issued_value_by_user[user]} บาท' for user in sorted(all_users)] + [''] + [''] + [f'{total_issued_value} บาท'] + ['']
    worksheet.append(total_row)
    
    
    # ตั้งค่ารูปแบบให้กับเซลล์ใน worksheet
    for row in worksheet.iter_rows(min_row=5, max_row=len(report_data) + 5, min_col=1, max_col=len(headers)):
        for cell in row:
            cell.font = font_data
            cell.alignment = align_center
            cell.border = border

    # ตั้งค่าความกว้างของคอลัมน์
    column_dimensions = {
        'A': 5,
        'B': 30,
        'C': 10,
        'D': 15,
        'E': 15,
        'F': 15,
        'G': 15,
        'H': 15,
        'I': 20,
        'J': 20,
        'K': 20,
        'L': 20,
    }
    for col, width in column_dimensions.items():
        worksheet.column_dimensions[col].width = width
    
    # สร้าง HttpResponse สำหรับไฟล์ Excel และบันทึก workbook ลงใน response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=monthly_report_{}_{}.xlsx'.format(month, year)
    workbook.save(response)
    
    return response



@user_passes_test(is_authorized)
@login_required
# รายงานประจำเดือน
def monthly_report(request, month=None, year=None):
    now = datetime.now()

    if request.GET.get('month'):
        month = int(request.GET.get('month'))
    if request.GET.get('year'):
        year = int(request.GET.get('year'))

    if not month:
        month = now.month
    if not year:
        year = now.year

    # Get Thai month name
    month_name = thai_month_name(month)

    # Convert year to Buddhist Era
    buddhist_year = convert_to_buddhist_era(year)

    # Define start_date and end_date for the selected month
    start_date = datetime(year, month, 1)
    end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)

    # Define previous month start_date and end_date
    previous_month_start = (start_date - timedelta(days=1)).replace(day=1)
    previous_month_end = start_date - timedelta(seconds=1)

    # Get all products
    products = Product.objects.all()

    report_data = []
    all_users = set()
    total_issued_value = Decimal(0)  # ใช้ Decimal แทน float
    total_issued_value_by_user = defaultdict(Decimal)  # ใช้ Decimal แทน float

    for product in products:
        previous_balance_record = MonthlyStockRecord.objects.filter(
            product=product,
            month=previous_month_end.month,
            year=previous_month_end.year
        ).first()

        previous_balance = previous_balance_record.end_of_month_balance if previous_balance_record else 0

        # Calculate received quantity for the current month
        received_current_month = Receiving.objects.filter(
            product=product, date_created__range=(start_date, end_date)
        ).aggregate(total_received=Sum('quantityreceived'))['total_received'] or 0

        # Calculate total balance (previous balance + received current month)
        total_balance = previous_balance + received_current_month

        # Calculate issued quantity for the current month
        issued_current_month = Issuing.objects.filter(
            product=product, datecreated__range=(start_date, end_date), order__status=True
        ).aggregate(total_issued=Sum('quantity'))['total_issued'] or 0

        # Calculate remaining balance
        remaining_balance = total_balance - issued_current_month

        # Calculate total issued value for the current month
        issued_items = Issuing.objects.filter(
            product=product, datecreated__range=(start_date, end_date), order__status=True
        )
        total_issued_value_product = issued_items.aggregate(total_cost=Sum(F('price') * F('quantity')))['total_cost'] or 0

        # Aggregate user issuings
        user_issuings = defaultdict(int)

        for issuing in issued_items:
            user_full_name = issuing.order.user.get_first_name()
            user_issuings[user_full_name] += issuing.quantity
            all_users.add(user_full_name)

            # Calculate total cost issued by each user
            total_cost = issuing.price * issuing.quantity
            total_issued_value_by_user[user_full_name] += total_cost
            total_issued_value += total_cost

        report_data.append({
            'product': product.product_name,
            'unit': product.unit,
            'previous_balance': previous_balance,
            'received_current_month':received_current_month,
            'total_balance': total_balance,
            'user_issuings': user_issuings,
            'issued_current_month': issued_current_month,
            'remaining_balance': remaining_balance,
            'total_issued_value': total_issued_value_product,
            'note': '',
        })

    # Sort all_users for consistent ordering
    sorted_all_users = sorted(all_users)

    context = {
        'title': 'รายงานประจำเดือน',
        'report_data': report_data,
        'all_users': sorted_all_users,
        'month': month,
        'year': year,
        'now': now,
        'years': range(2020, now.year + 1),
        'months': [
            (1, 'มกราคม'), (2, 'กุมภาพันธ์'), (3, 'มีนาคม'), (4, 'เมษายน'),
            (5, 'พฤษภาคม'), (6, 'มิถุนายน'), (7, 'กรกฎาคม'), (8, 'สิงหาคม'),
            (9, 'กันยายน'), (10, 'ตุลาคม'), (11, 'พฤศจิกายน'), (12, 'ธันวาคม')
        ],
        'pending_orders_count': count_pending_orders(),
        'month_name': month_name,
        'buddhist_year': buddhist_year,
        'total_issued_value_by_user': total_issued_value_by_user,
        'total_issued_value': total_issued_value,
    }

    return render(request, 'monthly_report.html', context)


@user_passes_test(is_authorized)
@login_required
# รายงงานจำนวนคงเหลือ ยกมา
def monthly_stock_records(request):
    now = datetime.now()
    last_month = now.month - 1 if now.month > 1 else 12
    last_year = now.year if now.month > 1 else now.year - 1

    # ตรวจสอบว่ามีการระบุเดือนและปีในพารามิเตอร์ GET หรือไม่ ถ้าไม่มีใช้เดือนและปีของเดือนที่แล้ว
    month = int(request.GET.get('month', last_month))
    year_buddhist = int(request.GET.get('year', last_year + 543))

    # แปลงปี พ.ศ. เป็น ค.ศ. สำหรับการค้นหาในฐานข้อมูล
    year_ad = year_buddhist - 543

    # กรองข้อมูล MonthlyStockRecord ตามเดือนและปี
    records = MonthlyStockRecord.objects.filter(month=month, year=year_ad)

    # กำหนดค่าให้กับตัวแปร context
    context = {
        'title': 'ข้อมูลวัสดุประจำเดือน (ยกมา)',
        'records': records,
        'selected_month': month,
        'selected_year': year_buddhist,
        'years': range(2020 + 543, datetime.now().year + 1 + 543),
        'months': [
            (1, 'มกราคม'), (2, 'กุมภาพันธ์'), (3, 'มีนาคม'), (4, 'เมษายน'),
            (5, 'พฤษภาคม'), (6, 'มิถุนายน'), (7, 'กรกฎาคม'), (8, 'สิงหาคม'),
            (9, 'กันยายน'), (10, 'ตุลาคม'), (11, 'พฤศจิกายน'), (12, 'ธันวาคม')
        ],
        'pending_orders_count': count_pending_orders(),
    }

    previous_month = month if month > 1 else 12
    previous_year = year_ad if month > 1 else year_ad - 1
    context['previous_month_name'] = thai_month_name(previous_month)
    context['previous_year_buddhist'] = convert_to_buddhist_era(previous_year)

    return render(request, 'monthly_stock_records.html', context)


@user_passes_test(is_authorized)
@login_required
# export excel รายงงานจำนวนคงเหลือ ยกมา
def export_monthly_stock_records_to_excel(request):
    now = datetime.now()
    last_month = now.month - 1 if now.month > 1 else 12
    last_year = now.year if now.month > 1 else now.year - 1

    # ดึงเดือนและปีจากพารามิเตอร์ GET หรือใช้ค่าเดือนและปีของเดือนที่แล้ว
    month = int(request.GET.get('month', last_month))
    year_buddhist = int(request.GET.get('year', last_year + 543))

    # แปลงปี พ.ศ. เป็น ค.ศ. สำหรับการค้นหาในฐานข้อมูล
    year_ad = year_buddhist - 543

    # กรองข้อมูล MonthlyStockRecord ตามเดือนและปี
    records = MonthlyStockRecord.objects.filter(month=month, year=year_ad)

    # สร้าง response สำหรับการบันทึกไฟล์ Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="monthly_stock_records_{month}_{year_buddhist}.xlsx"'

    # สร้างไฟล์ Excel workbook
    wb = Workbook()
    ws = wb.active

    # ตั้งชื่อ sheet
    ws.title = f"Monthly Stock Records {month}-{year_buddhist}"  # ใช้ (-) เป็นตัวคั่น

    # เพิ่มข้อมูลหัวเรื่อง
    previous_month_name = thai_month_name(month)
    previous_year_buddhist = convert_to_buddhist_era(year_ad)
    ws.merge_cells('A1:F1')
    ws['A1'] = f"ข้อมูลสินค้าคงเหลือประจำเดือน {previous_month_name} พ.ศ. {previous_year_buddhist}"

    # กำหนด header
    headers = ['ลำดับ', 'วัสดุ', 'เดือน', 'ปี', 'จำนวนคงเหลือ', 'วันที่บันทึก']
    ws.append(headers)

    # กำหนดรูปแบบเส้นตาราง
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # เพิ่มข้อมูลลงใน rows
    for idx, record in enumerate(records, start=1):
        date_str = format_datetime(record.date_recorded, "d MMMM y H:mm", locale='th')
        row = [
            idx,
            record.product.product_name,
            record.month,
            record.year + 543,  # แปลงปี ค.ศ. เป็น พ.ศ.
            record.end_of_month_balance,
            date_str  # แปลงวันที่เป็น string ในรูปแบบที่ต้องการ
        ]
        ws.append(row)

    # เพิ่มเส้นตารางให้กับ cells
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=6):
        for cell in row:
            cell.border = thin_border

    # บันทึก workbook ลงใน response
    wb.save(response)
    return response


@user_passes_test(is_authorized)
@login_required
# ฟังก์ชันบันทึกคงเหลือ ยกมา
def record_monthly_stock_view(request):
    if request.method == 'POST':
        form = RecordMonthlyStockForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            now = datetime.now()
            first_day_of_current_month = now.replace(day=1)
            last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)

            # ตรวจสอบว่ามีการบันทึกข้อมูลสำหรับเดือนก่อนหน้าแล้วหรือไม่
            existing_records = MonthlyStockRecord.objects.filter(
                month=last_day_of_previous_month.month,
                year=last_day_of_previous_month.year
            )

            if existing_records.exists():
                messages.error(request, 'มีการบันทึกข้อมูลของแล้ว.')
                return redirect('dashboard:record_monthly_stock')

            # สร้างบันทึกข้อมูลสำหรับเดือนก่อนหน้า
            products = Product.objects.all()
            for product in products:
                MonthlyStockRecord.objects.create(
                    product=product,
                    month=last_day_of_previous_month.month,
                    year=last_day_of_previous_month.year,
                    end_of_month_balance=product.quantityinstock
                )

            messages.success(request, 'บันทึกข้อมูลสต็อกสินค้าเรียบร้อยแล้ว.')
            return redirect('dashboard:record_monthly_stock')
    else:
        form = RecordMonthlyStockForm()

    context = {
        'title':'บันทึกยอดวัสดุคงเหลือประจำเดือน',
        'form': form,
               'pending_orders_count': count_pending_orders(),}

    return render(request, 'record_monthly_stock.html', context)


@user_passes_test(is_authorized)
@login_required
# รายงานรับเข้าประจำเดือน
def monthly_report_receive(request):
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # ใช้เดือนและปีปัจจุบันหากไม่ได้ระบุในพารามิเตอร์ GET
    last_month = now.month if now.month > 1 else 12
    last_year = now.year if now.month > 1 else now.year - 1

    # ตรวจสอบว่ามีการระบุเดือนและปีในพารามิเตอร์ GET หรือไม่ ถ้าไม่มีใช้เดือนและปีของเดือนที่แล้ว
    month = int(request.GET.get('month', last_month))
    year_buddhist = int(request.GET.get('year', last_year + 543))

    # แปลงปี พ.ศ. เป็น ค.ศ. สำหรับการค้นหาในฐานข้อมูล
    year_ad = year_buddhist - 543

    # ดึงข้อมูลรับเข้าสินค้าที่มีเดือนและปีที่ระบุ
    receiving_data = Receiving.objects.filter(
        month=month,
        year=year_ad
    ).select_related('product', 'suppliers').values(
        'product__product_name',
        'suppliers__supname',
        'quantityreceived',
        'unitprice',
        'date_created'
    )

    # กำหนดค่าให้กับตัวแปร context
    context = {
        'title': 'รายการรับเข้าวัสดุ',
        'receiving_data': receiving_data,
        'selected_month': month,
        'selected_year': year_buddhist,
        'years': range(2020 + 543, datetime.now().year + 1 + 543),
        'months': [
            (1, 'มกราคม'), (2, 'กุมภาพันธ์'), (3, 'มีนาคม'), (4, 'เมษายน'),
            (5, 'พฤษภาคม'), (6, 'มิถุนายน'), (7, 'กรกฎาคม'), (8, 'สิงหาคม'),
            (9, 'กันยายน'), (10, 'ตุลาคม'), (11, 'พฤศจิกายน'), (12, 'ธันวาคม')
        ],
        'month_name': thai_month_name(month),
        'pending_orders_count': count_pending_orders(),
    }

    previous_month = month - 1 if month > 1 else 12
    previous_year = year_ad if month > 1 else year_ad - 1
    context['previous_month_name'] = thai_month_name(previous_month)
    context['previous_year_buddhist'] = convert_to_buddhist_era(previous_year)
    
    return render(request, 'monthly_report_receive.html', context)


@user_passes_test(is_authorized)
@login_required
# export excel รายงานรับเข้าประจำเดือน
def export_to_excel_receive(request):
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # ใช้เดือนและปีปัจจุบันหากไม่ได้ระบุในพารามิเตอร์ GET
    last_month = now.month if now.month > 1 else 12
    last_year = now.year if now.month > 1 else now.year - 1

    # ตรวจสอบว่ามีการระบุเดือนและปีในพารามิเตอร์ GET หรือไม่ ถ้าไม่มีใช้เดือนและปีของเดือนที่แล้ว
    month = int(request.GET.get('month', last_month))
    year_buddhist = int(request.GET.get('year', last_year + 543))

    # แปลงปี พ.ศ. เป็น ค.ศ. สำหรับการค้นหาในฐานข้อมูล
    year_ad = year_buddhist - 543

    # ดึงข้อมูลรับเข้าสินค้าที่มีเดือนและปีที่ระบุ
    receiving_data = Receiving.objects.filter(
        month=month,
        year=year_ad
    ).select_related('product', 'suppliers').values(
        'product__product_name',
        'suppliers__supname',
        'quantityreceived',
        'unitprice',
        'date_created'
    )

    # สร้าง response สำหรับการบันทึกไฟล์ Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="receiving_report_{month}_{year_buddhist}.xlsx"'

    # สร้างไฟล์ Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active

    # ตั้งชื่อ sheet
    ws.title = f"Receiving Report {month}-{year_buddhist}"  # ใช้ (-) เป็นตัวคั่น

    # เพิ่มข้อมูลหัวเรื่อง
    previous_month_name = thai_month_name(month)
    previous_year_buddhist = convert_to_buddhist_era(year_ad)
    ws.merge_cells('A1:F1')
    cell = ws.cell(row=1, column=1)
    cell.value = f"รายการรับเข้าวัสดุ ประจำเดือน {previous_month_name} พ.ศ. {previous_year_buddhist}"
    cell.font = Font(bold=True, size=14)
    cell.alignment = Alignment(horizontal='center', vertical='center')

    # กำหนด header
    headers = ['ลำดับ', 'รายการวัสดุ', 'ซัพพลายเออร์', 'จำนวนที่รับเข้า', 'ราคา/หน่วย', 'วันที่รับเข้า']
    ws.append(headers)

    # กำหนดรูปแบบเส้นตาราง
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # เพิ่มข้อมูลลงใน rows
    for idx, data in enumerate(receiving_data, start=1):
        date_created = data['date_created']
        date_str = format_datetime(date_created, "d MMMM y H:mm", locale='th') if date_created else "ไม่ระบุ"
        row = [
            idx,
            data['product__product_name'],
            data['suppliers__supname'],
            data['quantityreceived'],
            data['unitprice'],
            date_str
        ]
        ws.append(row)

    # เพิ่มเส้นตารางให้กับ cells
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=6):
        for cell in row:
            cell.border = thin_border

    # บันทึก workbook ลงใน response
    wb.save(response)
    return response


@user_passes_test(is_authorized)
@login_required
# รายงานยอดรวมที่มีการเบิกแต่ละเดือน
def report_monthly_totals(request):
    orders = Order.objects.all()
    report_monthly_totals = defaultdict(Decimal)
    
    for order in orders:
        for item in order.items.all():
            # ใช้ tuple (order.month, order.year) เป็น key
            report_monthly_totals[(order.month, order.year)] += item.get_cost()
    
    # แปลงค่าใน report_monthly_totals เป็น float เพื่อให้สามารถใช้งานใน template ได้
    report_monthly_totals_float = {(month, year): float(total) for (month, year), total in report_monthly_totals.items()}
    
    context = {
        'title': 'Monthly Totals',
        'report_monthly_totals': report_monthly_totals_float,
    }
    return render(request, 'report_monthly_totals.html', context)



@user_passes_test(is_authorized)
@login_required
def total_quantity(request):
    products = Product.objects.all()
    stock = Total_Quantity.objects.all()

    query = request.GET.get('q')
    if query is not None:
        lookups = Q(product__product_id__icontains=query) | Q(product__product_name__icontains=query)
        stock = Total_Quantity.objects.filter(lookups)

    page = request.GET.get('page')

    p = Paginator(stock, 20)
    try:
        stock = p.page(page)
    except:
        stock = p.page(1)

    context = {
        'title':'รวมจำนวนวัสดุที่รับเข้า', 
        'stock':stock,
        'product':products,
        'pending_orders_count': count_pending_orders(),
        }
    return render(request, 'total_quantity.html', context)


@user_passes_test(is_authorized)
@login_required
# หน้าออเดอร์แต่ละคนในเดือนนั่นๆในเอชบอร์ด
def report_order_list(request):
    now = datetime.now()

    # ใช้เดือนและปีปัจจุบันหากไม่ได้ระบุในพารามิเตอร์ GET
    last_month = now.month if now.month > 1 else 12
    last_year = now.year if now.month > 1 else now.year - 1

    # ตรวจสอบว่ามีการระบุเดือนและปีในพารามิเตอร์ GET หรือไม่ ถ้าไม่มีใช้เดือนและปีของเดือนที่แล้ว
    month = int(request.GET.get('month', last_month))
    year_buddhist = int(request.GET.get('year', last_year + 543))

    # แปลงปี พ.ศ. เป็น ค.ศ. สำหรับการค้นหาในฐานข้อมูล
    year_ad = year_buddhist - 543

    # ดึงข้อมูลรับเข้าสินค้าที่มีเดือนและปีที่ระบุ
    order_data = Order.objects.filter(
        month=month,
        year=year_ad
     ).select_related('user')

    # กำหนดค่าให้กับตัวแปร context
    context = {
        'title': 'รายการเบิกประจำเดือน รายบุคคล',
        'order_data': order_data,
        'selected_month': month,
        'selected_year': year_buddhist,
        'years': range(2020 + 543, datetime.now().year + 1 + 543),
        'months': [
            (1, 'มกราคม'), (2, 'กุมภาพันธ์'), (3, 'มีนาคม'), (4, 'เมษายน'),
            (5, 'พฤษภาคม'), (6, 'มิถุนายน'), (7, 'กรกฎาคม'), (8, 'สิงหาคม'),
            (9, 'กันยายน'), (10, 'ตุลาคม'), (11, 'พฤศจิกายน'), (12, 'ธันวาคม')
        ],
        'month_name': thai_month_name(month),
        'pending_orders_count': count_pending_orders(),
    }

    previous_month = month - 1 if month > 1 else 12
    previous_year = year_ad if month > 1 else year_ad - 1
    context['previous_month_name'] = thai_month_name(previous_month)
    context['previous_year_buddhist'] = convert_to_buddhist_era(previous_year)
    
    return render(request, 'report_order_list.html', context)


@user_passes_test(is_authorized)
@login_required
# export excel หน้าออเดอร์แต่ละคนในเดือนนั่นๆในเอชบอร์ด
def export_excel_order(request):
    month = int(request.GET.get('month'))
    year_buddhist = int(request.GET.get('year'))
    year_ad = year_buddhist - 543

    # ดึงข้อมูล Order ที่ตรงกับเดือนและปีที่ระบุ
    order_data = Order.objects.filter(
        month=month,
        year=year_ad
    ).select_related('user')

    # สร้าง Workbook และ Sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Orders'

    # กำหนดหัวตาราง
    columns = ['ลำดับ', 'ชื่อผู้ใช้งาน', 'เลขที่เบิก', 'ยอดรวม', 'วันที่เบิก', 'สถานะ', 'หมายเหตุ']
    ws.append(columns)

    # กำหนดฟอนต์ภาษาไทย ขนาด 16
    font = Font(name='TH Sarabun New', size=16)
    alignment = Alignment(horizontal='center', vertical='center')
    thin_border = Border(left=Side(style='thin'), 
                         right=Side(style='thin'), 
                         top=Side(style='thin'), 
                         bottom=Side(style='thin'))

    for col in ws.iter_cols(min_row=1, max_row=1, min_col=1, max_col=len(columns)):
        for cell in col:
            cell.font = font
            cell.alignment = alignment
            cell.border = thin_border

    # เพิ่มข้อมูลในตาราง
    for idx, order in enumerate(order_data, start=1):
        user_full_name = order.user.get_full_name()
        total_price = order.get_total_price
        # date_created = order.date_created.strftime("%d %b %Y เวลา %H:%M น.")
        date_created = format_datetime( order.date_created, "d MMMM y เวลา H:mm น.", locale='th') if  order.date_created else "ไม่ระบุ"
        status = 'อนุมัติ' if order.status else 'ปฏิเสธ' if order.status is False else 'รอดำเนินการ..'
        other = order.other or ''

        row = [idx, user_full_name, order.id, total_price, date_created, status, other]
        ws.append(row)

        for col in ws.iter_cols(min_row=idx + 1, max_row=idx + 1, min_col=1, max_col=len(columns)):
            for cell in col:
                cell.font = font
                cell.alignment = alignment
                cell.border = thin_border

    # ปรับขนาดคอลัมน์ให้พอดี
    for col in ws.columns:
        max_length = max(len(str(cell.value)) for cell in col)
        adjusted_width = (max_length + 2)
        ws.column_dimensions[col[0].column_letter].width = adjusted_width

    # สร้าง HTTP Response และบันทึกไฟล์ Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Orders_{month}_{year_buddhist}.xlsx'
    wb.save(response)
    return response


@user_passes_test(is_authorized)
@login_required
# หน้าเดชบอร์ด
# def dashboard_home(request):
#     now = datetime.now()

#     # ใช้เดือนและปีปัจจุบันหากไม่ได้ระบุในพารามิเตอร์ GET
#     last_month = now.month if now.month > 1 else 12
#     last_year = now.year if now.month > 1 else now.year - 1

#     # ตรวจสอบว่ามีการระบุเดือนและปีในพารามิเตอร์ GET หรือไม่ ถ้าไม่มีใช้เดือนและปีของเดือนที่แล้ว
#     month = int(request.GET.get('month', last_month))
#     year_buddhist = int(request.GET.get('year', last_year + 543))

#     # แปลงปี พ.ศ. เป็น ค.ศ. สำหรับการค้นหาในฐานข้อมูล
#     year_ad = year_buddhist - 543

#     # กรองข้อมูลการเบิกวัสดุที่ได้รับการอนุมัติออเดอร์แล้ว ตามเดือนและปีที่เลือก
#     issuing_data = Issuing.objects.filter(order__status=True, month=month, year=year_ad).values(
#         'order__user__profile__workgroup__work_group',
#         'product__product_name',
#         'product__unit'
#     ).annotate(
#         total_quantity=Sum('quantity'),
#         total_amount=Sum(F('price') * F('quantity'))
#     ).order_by('order__user__profile__workgroup__work_group')

#     # ตรวจสอบว่ามีข้อมูลหรือไม่
#     if issuing_data.exists():
#         # แปลงข้อมูลเป็น DataFrame
#         df = pd.DataFrame(issuing_data)

#         # สร้างกราฟด้วย Plotly สำหรับจำนวนที่เบิก
#         fig_quantity = px.bar(df, x='order__user__profile__workgroup__work_group', y='total_quantity',
#                               color='product__product_name',
#                               labels={'order__user__profile__workgroup__work_group': 'กลุ่มงาน',
#                                       'total_quantity': 'จำนวนที่เบิก',
#                                       'product__product_name': 'ชื่อวัสดุ'},
#                               title=f'จำนวนพัสดุที่เบิกในแต่ละกลุ่มงาน (เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)})')
        

#         # สร้างกราฟด้วย Plotly สำหรับจำนวนเงินที่เบิก
#         fig_amount = px.bar(df, x='order__user__profile__workgroup__work_group', y='total_amount',
#                             color='product__product_name',
#                             labels={'order__user__profile__workgroup__work_group': 'กลุ่มงาน',
#                                     'total_amount': 'จำนวนเงินที่เบิก',
#                                     'product__product_name': 'ชื่อวัสดุ'},
#                             title=f'จำนวนเงินที่เบิกวัสดุในแต่ละกลุ่มงาน (เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)})')
                            
        
#         # สร้างกราฟด้วย Plotly สำหรับจำนวนเงินที่เบิกตามผู้ใช้งาน
#         user_issuing_data = Issuing.objects.filter(order__status=True, month=month, year=year_ad).values(
#             'order__user__first_name'  # หรือเลือกเป็น profile__user__username ตามโมเดลของคุณ
#         ).annotate(
#             total_quantity=Sum('quantity'),
#             total_amount=Sum(F('price') * F('quantity')), 
#         ).order_by('order__user__first_name')
        
#         if user_issuing_data.exists():
#             df_user = pd.DataFrame(user_issuing_data)
#             fig_user_amount_pie = px.pie(df_user, names='order__user__first_name', values='total_amount',
#                              labels={'order__user__first_name': 'ชื่อ'},
#                              hover_data={'total_amount': True, 'total_quantity': True},
#                              title=f'สัดส่วนการเบิกวัสดุรายบุคคล (เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)})')

#             # เพิ่มเติม labels และ tooltips สำหรับ total_quantity
#             fig_user_amount_pie.update_traces(textinfo='label+percent', 
#                                                 hoverinfo='label+value+percent', 
#                                                 pull=[0.1]*len(df_user), 
#                                                 textfont_size=12,
#                                                 marker=dict(line=dict(color='#000000', width=1.2)),
#                                                 textfont=dict(size=13),
#                                                 customdata=df_user['total_quantity'],  # เพิ่มข้อมูลเพิ่มเติมที่แสดงใน tooltips
#                                                 hovertemplate='<b>%{label}</b><br>' +
#                                                                 'รวมเงิน: %{value} บาท<br>' +
#                                                                 'จำนวนวัสดุ: %{customdata} ชิ้น<br>' +
#                                                                 '<extra></extra>'
#             )
#             fig_user_amount_pie.update_layout(title=f'สัดส่วนการเบิกวัสดุรายบุคคล (เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)})', margin=dict(l=20, r=20, t=40, b=20), autosize=True)

#         # แปลงกราฟเป็น HTML
#         graph_html_quantity = fig_quantity.to_html(full_html=False)
#         graph_html_amount = fig_amount.to_html(full_html=False)
#         graph_html_user_amount_pie = fig_user_amount_pie.to_html(full_html=False)
#     else:
#         graph_html_quantity = f"<p>ยังไม่มีจำนวนการเบิกวัสดุในแต่ละกลุ่มงาน เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)}</p>"
#         graph_html_amount = f"<p>ยังไม่มีจำนวนเงินการเบิกวัสดุในแต่ละกลุ่มงาน เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)}</p>"
#         graph_html_user_amount_pie = f"<p>ยังไม่มีสัดส่วนการเบิกวัสดุตามผู้ใช้งาน เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)}</p>"

#     context = {
#         'title': 'Dashboard',
#         'graph_html_quantity': graph_html_quantity,
#         'graph_html_amount': graph_html_amount,
#         'graph_html_user_amount_pie': graph_html_user_amount_pie,
#         'pending_orders_count': count_pending_orders(),
#         'now': now,  # ส่งตัวแปร now เข้าไปใน context
#         'selected_month': month,
#         'selected_year': year_buddhist,
#         'years': range(2020 + 543, datetime.now().year + 1 + 543),
#         'months': [
#             (1, 'มกราคม'), (2, 'กุมภาพันธ์'), (3, 'มีนาคม'), (4, 'เมษายน'),
#             (5, 'พฤษภาคม'), (6, 'มิถุนายน'), (7, 'กรกฎาคม'), (8, 'สิงหาคม'),
#             (9, 'กันยายน'), (10, 'ตุลาคม'), (11, 'พฤศจิกายน'), (12, 'ธันวาคม')
#         ],
#     }
#     return render(request, 'dashboard_home.html', context)

def dashboard_home(request):
    now = datetime.now()

    # ใช้เดือนและปีปัจจุบันหากไม่ได้ระบุในพารามิเตอร์ GET
    last_month = now.month if now.month > 1 else 12
    last_year = now.year if now.month > 1 else now.year - 1

    # ตรวจสอบว่ามีการระบุเดือนและปีในพารามิเตอร์ GET หรือไม่ ถ้าไม่มีใช้เดือนและปีของเดือนที่แล้ว
    month = int(request.GET.get('month', last_month))
    year_buddhist = int(request.GET.get('year', last_year + 543))

    # แปลงปี พ.ศ. เป็น ค.ศ. สำหรับการค้นหาในฐานข้อมูล
    year_ad = year_buddhist - 543

    # กรองข้อมูลการเบิกวัสดุที่ได้รับการอนุมัติออเดอร์แล้ว ตามเดือนและปีที่เลือก
    issuing_data = Issuing.objects.filter(order__status=True, month=month, year=year_ad).values(
        'order__user__profile__workgroup__work_group',
        'product__product_name',
        'product__unit'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_amount=Sum(F('price') * F('quantity'))
    ).order_by('order__user__profile__workgroup__work_group')

    # ตรวจสอบว่ามีข้อมูลหรือไม่
    if issuing_data.exists():
        # แปลงข้อมูลเป็น DataFrame
        df = pd.DataFrame(issuing_data)

        # สร้างกราฟด้วย Plotly สำหรับจำนวนที่เบิก
        fig_quantity = px.bar(df, x='order__user__profile__workgroup__work_group', y='total_quantity',
                              color='product__product_name',
                              labels={'order__user__profile__workgroup__work_group': 'กลุ่มงาน',
                                      'total_quantity': 'จำนวนที่เบิก',
                                      'product__product_name': 'ชื่อวัสดุ'},
                              title=f'จำนวนพัสดุที่เบิกในแต่ละกลุ่มงาน (เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)})')
        # fig_quantity.update_traces(
        #     hovertemplate='<b>%{x}</b><br>จำนวนที่เบิก: %{y:,}<br><extra></extra>',
        #     texttemplate='%{y:,}'
        # )

        # สร้างกราฟด้วย Plotly สำหรับจำนวนเงินที่เบิก
        fig_amount = px.bar(df, x='order__user__profile__workgroup__work_group', y='total_amount',
                            color='product__product_name',
                            labels={'order__user__profile__workgroup__work_group': 'กลุ่มงาน',
                                    'total_amount': 'จำนวนเงินที่เบิก',
                                    'product__product_name': 'ชื่อวัสดุ'},
                            title=f'จำนวนเงินที่เบิกวัสดุในแต่ละกลุ่มงาน (เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)})')

        # fig_amount.update_traces(
        #     hovertemplate='<b>%{label}</b><br>จำนวนเงิน: %{y:,} บาท<br><extra></extra>',
        #     texttemplate='%{y:,} บาท'
        # )
        
        
        # สร้างกราฟด้วย Plotly สำหรับจำนวนเงินที่เบิกตามผู้ใช้งาน
        user_issuing_data = Issuing.objects.filter(order__status=True, month=month, year=year_ad).values(
            'order__user__first_name'  # หรือเลือกเป็น profile__user__username ตามโมเดลของคุณ
        ).annotate(
            total_quantity=Sum('quantity'),
            total_amount=Sum(F('price') * F('quantity')), 
        ).order_by('order__user__first_name')

        if user_issuing_data.exists():
            df_user = pd.DataFrame(user_issuing_data)
            fig_user_amount_pie = px.pie(df_user, names='order__user__first_name', values='total_amount',
                             labels={'order__user__first_name': 'ชื่อ'},
                             hover_data={'total_amount': True, 'total_quantity': True},
                             title=f'สัดส่วนการเบิกวัสดุรายบุคคล (เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)})')

            # เพิ่มเติม labels และ tooltips สำหรับ total_quantity
            fig_user_amount_pie.update_traces(textinfo='label+percent', 
                                                hoverinfo='label+value+percent', 
                                                pull=[0.1]*len(df_user), 
                                                textfont_size=12,
                                                marker=dict(line=dict(color='#000000', width=1.2)),
                                                textfont=dict(size=13),
                                                customdata=df_user['total_quantity'],  # เพิ่มข้อมูลเพิ่มเติมที่แสดงใน tooltips
                                                hovertemplate='<b>%{label}</b><br>' +
                                                                'รวมเงิน: %{value:,} บาท<br>' +
                                                                'จำนวนวัสดุ: %{customdata} ชิ้น<br>' +
                                                                '<extra></extra>')
            fig_user_amount_pie.update_layout(title=f'สัดส่วนการเบิกวัสดุรายบุคคล (เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)})', margin=dict(l=20, r=20, t=40, b=20), autosize=True)

            # สร้างกราฟวงกลมด้วย Plotly สำหรับจำนวนเงินที่เบิกในแต่ละกลุ่มงาน
            fig_group_amount_pie = px.pie(df, names='order__user__profile__workgroup__work_group', values='total_amount',
                                labels={'order__user__profile__workgroup__work_group': 'กลุ่มงาน'},
                                title=f'สัดส่วนการเบิกวัสดุในแต่ละกลุ่มงาน (เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)})')

            fig_group_amount_pie.update_traces(
                                                hoverinfo='label+value+percent', 
                                                pull=[0.1]*len(df), 
                                                textfont_size=12,
                                                marker=dict(line=dict(color='#000000', width=1.2)),
                                                textfont=dict(size=13),
                                                hovertemplate='<b>%{label}</b><br>รวมเงิน: %{value:,} บาท<br><extra></extra>')
            fig_group_amount_pie.update_layout(title=f'สัดส่วนการเบิกวัสดุในแต่ละกลุ่มงาน (เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)})', margin=dict(l=20, r=20, t=40, b=20), autosize=True)


        # แปลงกราฟเป็น HTML
        graph_html_quantity = fig_quantity.to_html(full_html=False)
        graph_html_amount = fig_amount.to_html(full_html=False)
        graph_html_group_amount_pie = fig_group_amount_pie.to_html(full_html=False)
        graph_html_user_amount_pie = fig_user_amount_pie.to_html(full_html=False)
    else:
        graph_html_quantity = f"<p>ยังไม่มีจำนวนการเบิกวัสดุในแต่ละกลุ่มงาน เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)}</p>"
        graph_html_amount = f"<p>ยังไม่มีจำนวนเงินการเบิกวัสดุในแต่ละกลุ่มงาน เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)}</p>"
        graph_html_group_amount_pie = f"<p>ยังไม่มีสัดส่วนการเบิกวัสดุในแต่ละกลุ่มงาน เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)}</p>"
        graph_html_user_amount_pie = f"<p>ยังไม่มีสัดส่วนการเบิกวัสดุตามผู้ใช้งาน เดือน {thai_month_name(month)} {convert_to_buddhist_era(year_ad)}</p>"

    context = {
        'title': 'Dashboard',
        'graph_html_quantity': graph_html_quantity,
        'graph_html_amount': graph_html_amount,
        'graph_html_group_amount_pie': graph_html_group_amount_pie,
        'graph_html_user_amount_pie': graph_html_user_amount_pie,
        'pending_orders_count': count_pending_orders(),
        'now': now,  # ส่งตัวแปร now เข้าไปใน context
        'selected_month': month,
        'selected_year': year_buddhist,
        'years': range(2020 + 543, datetime.now().year + 1 + 543),
        'months': [
            (1, 'มกราคม'), (2, 'กุมภาพันธ์'), (3, 'มีนาคม'), (4, 'เมษายน'),
            (5, 'พฤษภาคม'), (6, 'มิถุนายน'), (7, 'กรกฎาคม'), (8, 'สิงหาคม'),
            (9, 'กันยายน'), (10, 'ตุลาคม'), (11, 'พฤศจิกายน'), (12, 'ธันวาคม')
        ],
    }
    return render(request, 'dashboard_home.html', context)



@user_passes_test(is_authorized)
@login_required
# export to excel product
def export_products_to_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="products.xlsx"'

    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Products"

    # Define headers
    headers = ['หมวดหมู่หลัก', 'หมวดหมู่ย่อย', 'รหัสพัสดุ', 'ชื่อรายการ', 'คำอธิบาย', 'หน่วย', 'วันที่เพิ่มรายการ', ]
    ws.append(headers)

    # Query data
    products = Product.objects.all().select_related('category__category')  # ใช้ select_related เพื่อดึงข้อมูลแบบ prefetch จากแบบจำลอง Category และ Subcategory

    # Add data rows
    for product in products:
        row = [
            product.category.category.name_cate if product.category else '',  # หมวดหมู่หลัก
            product.category.name_sub if product.category else '',  # หมวดหมู่ย่อย
            product.product_id,
            product.product_name,
            product.description,
            product.unit,
            product.date_created.strftime('%Y-%m-%d %H:%M:%S'),  # แปลง datetime เป็น string ก่อนนำไปใช้
        ]
        ws.append(row)

    # Save workbook to response
    wb.save(response)
    return response


@user_passes_test(is_authorized_manager)
@login_required
def products(request):
    query = request.GET.get('q')
    products = Product.objects.all()

    if query is not None:
        lookups = Q(product_id__icontains=query) | Q(product_name__icontains=query)
        products = Product.objects.filter(lookups)

    # ใช้ annotate เพื่อคำนวณจำนวนรวมและวันที่รับเข้าล่าสุด
    products = products.annotate(
        total_quantity_received=Sum('Receiving__quantity'),
        latest_receiving_date=Max('Receiving__id')
    ).order_by('-id')

    page = request.GET.get('page')

    p = Paginator(products, 20)
    try:
        products = p.page(page)
    except:
        products = p.page(1)

    context = {
        'title':'รายการวัสดุทั้งหมด' ,
        'products':products,
        'pending_orders_count': count_pending_orders(),
		'total_quantity':total_quantity
        }
    return render(request, 'products.html', context)


@user_passes_test(is_authorized_manager)
@login_required
def upload_products(request):
    if request.method == 'POST':
        file = request.FILES['file']
        try:
            df = pd.read_excel(file)
            for index, row in df.iterrows():
                main_category_name = row['หมวดหมู่หลัก']
                sub_category_name = row['หมวดหมู่ย่อย']

                # Create or get the main category
                main_category, created = Category.objects.get_or_create(name_cate=main_category_name)

                # Create or get the subcategory
                sub_category, created = Subcategory.objects.get_or_create(name_sub=sub_category_name, category=main_category)

                # Create the product
                Product.objects.create(
                    category=sub_category,
                    product_id=row['รหัสพัสดุ'],
                    product_name=row['ชื่อรายการ'],
                    description=row['คำอธิบาย'],
                    unit=row['หน่วย'],
                )
            messages.success(request, 'นำเข้าข้อมูลสำเร็จ')
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {e}')
    return redirect('dashboard:products')



@user_passes_test(is_authorized_manager)
@login_required
def add_product(request):
    if request.method == 'POST':
        form = AddProductForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, 'เพิ่มวัสดุเรียบร้อยแล้ว!')
                return redirect('dashboard:add_product')
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {e}')
    else:
        form = AddProductForm()
    context = {'title':'เพิ่มวัสดุ', 'form':form,
                'pending_orders_count': count_pending_orders(),}
    return render(request, 'add_product.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def delete_product(request, id):
    product = Product.objects.filter(id=id).delete()
    messages.success(request, 'ลบวัสดุสำเร็จ')
    return redirect('dashboard:products')



@user_passes_test(is_authorized_manager)
@login_required
def edit_product(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        form = EditProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'อัพเดทวัสดุ สำเร็จ')
            return redirect('dashboard:products')
    else:
        form = EditProductForm(instance=product)
    context = {'title': 'Edit Product', 
               'form':form,
                'pending_orders_count': count_pending_orders(),}
    return render(request, 'edit_product.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def suppliers(request):
    suppliers = Suppliers.objects.all()

    query = request.GET.get('q')
    if query is not None:
        lookups = Q(supname__icontains=query) | Q(contactname__icontains=query)
        suppliers = Suppliers.objects.filter(lookups)


    page = request.GET.get('page')

    p = Paginator(suppliers, 20)
    try:
        suppliers = p.page(page)
    except:
        suppliers = p.page(1)

    context = {
        'title':'ซัพพลายเออร์', 
        'suppliers':suppliers,
        'pending_orders_count': count_pending_orders(),
        }
    return render(request, 'suppliers.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def add_suppliers(request):
    if request.method == 'POST':
        form = AddSuppliersForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มวัสดุเรียบร้อยแล้ว!')
            return redirect('dashboard:add_suppliers')
    else:
        form = AddSuppliersForm()
    context = {'title':'เพิ่มซัพพลายเอร์', 'form':form,
                'pending_orders_count': count_pending_orders(),}
    return render(request, 'add_suppliers.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def delete_suppliers(request, id):
    suppliers = Suppliers.objects.filter(id=id).delete()
    messages.success(request, 'ลบซัพพลายเออร์สำเร็จ')
    return redirect('dashboard:supplierss')



@user_passes_test(is_authorized_manager)
@login_required
def edit_suppliers(request, id):
    sup= Suppliers.objects.get(id=id)
    form = EditSuppliersForm()

    if request.method == 'POST':
        form = EditSuppliersForm(request.POST, request.FILES, instance=sup)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขข้อมูล สำเร็จ')
            return redirect('dashboard:suppliers')
    else:
        form = EditSuppliersForm(instance=sup)
    context = {'title': 'แก้ไขข้อมูลซัพพลายเออร์', 
               'sup':sup,
               'form':form,
               'pending_orders_count': count_pending_orders(),}
    return render(request, 'edit_suppliers.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def detail_suppliers(request, id):
    sup = get_object_or_404(Suppliers, id=id)
    context = {
        'title':'รายละเอียดซัพพลายเออร์', 
        'sup':sup,
        'pending_orders_count': count_pending_orders(),
        }
    return render(request, 'detail_suppliers.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def receive_list(request):
    receive = Receiving.objects.all()

    query = request.GET.get('q')
    if query is not None:
        lookups = Q(product__product_name__icontains=query) | Q(product__product_id__icontains=query)
        receive = Receiving.objects.filter(lookups)

    page = request.GET.get('page')

    p = Paginator(receive, 20)
    try:
        receive = p.page(page)
    except:
        receive = p.page(1)

    context = {
        'title':'รับเข้าวัสดุ', 
        'receive':receive,
        'pending_orders_count': count_pending_orders(),
        }
    return render(request, 'receive_list.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def receive_product(request):
    if request.method == 'POST':
        form = ReceivingForm(request.POST)
        if form.is_valid():
            received_product = form.save(commit=False)
            received_product.save()
            

            # อัปเดตจำนวนสินค้าในสต็อก
            # product = received_product.product
            # stock, created = Stock.objects.get_or_create(product=product)
            # stock.quantity += received_product.quantityreceived
            # stock.save()

            # อัปเดตจำนวนทั้งหมดที่รับเข้า
            product = received_product.product
            total, created = Total_Quantity.objects.get_or_create(product=product)
            total.totalquantity += received_product.quantityreceived
            total.save()

            # อัปเดตจำนวนสินค้าในตาราง Product
            Product.objects.filter(id=product.id).update(quantityinstock=F('quantityinstock') + received_product.quantity)

            messages.success(request, 'เพิ่มข้อมูลสำเร็จ')
            return redirect('dashboard:receive_list')  # หรือไปยังหน้าที่ต้องการ
        else:
            messages.error(request, 'เพิ่มข้อมูลไม่สำเร็จ')
    else:
        form = ReceivingForm()

    context = {
        'title':'รับเข้าวัสดุ',
        'form': form,
        'Product':Product.objects.all(),
        'Suppliers':Suppliers.objects.all(),
        'pending_orders_count': count_pending_orders(),
        }
    return render(request, 'receive_product.html', context)


@user_passes_test(is_authorized_manager)
@login_required
def update_received_product(request, id):
    received_product = get_object_or_404(Receiving, id=id)

    if request.method == 'POST':
        form = ReceivingForm(request.POST, instance=received_product)
        if form.is_valid():
            updated_received_product = form.save(commit=False)
            updated_received_product.save()

            # อัพเดทจำนวนสินค้าในสต็อก
            product = updated_received_product.product
            # stock, created = Stock.objects.get_or_create(product=product)
            # stock.quantity -= received_product.quantityreceived  # ลบจำนวนเดิม
            # stock.quantity += updated_received_product.quantity  # เพิ่มจำนวนใหม่
            # stock.save()

            # อัพเดทจำนวนทั้งหมดที่รับเข้า
            # total, created = Total_Quantity.objects.get_or_create(product=product)
            # total.totalquantity -= received_product.quantityreceived  # ลบจำนวนเดิม
            # total.totalquantity += updated_received_product.quantityreceived  # เพิ่มจำนวนใหม่
            # total.save()

            # อัปเดตจำนวนสินค้าในตาราง Product
            Product.objects.filter(id=product.id).update(quantityinstock=F('quantityinstock') + received_product.quantity)

            messages.success(request, 'อัพเดทข้อมูลสำเร็จ')
            return redirect('dashboard:receive_list')  # หรือไปยังหน้าที่ต้องการ
        else:
            messages.error(request, 'อัพเดทข้อมูลไม่สำเร็จ')
    else:
        form = ReceivingForm(instance=received_product)

    context = {
        'title':'อัพเดทการรับเข้าสินค้า',
        'form': form,
        'Product': Product.objects.all(),
        'Suppliers': Suppliers.objects.all(),
        'pending_orders_count': count_pending_orders(),
    }
    return render(request, 'update_received_product.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def delete_receive(request, id):
    suppliers = Receiving.objects.filter(id=id).delete()
    messages.success(request, 'ลบรับเข้าสำเร็จ')
    return redirect('dashboard:receive_list')




@user_passes_test(is_authorized_manager)
@login_required
def stock(request):
    products = Product.objects.all()
    
    # คำนวณ total_quantity สำหรับแต่ละสินค้า
    for product in products:
        product.total_quantity = Receiving.total_quantity_by_product(product.id)

    query = request.GET.get('q')
    if query is not None:
        lookups = Q(product_id__icontains=query) | Q(product_name__icontains=query)
        products = Product.objects.filter(lookups)

    page = request.GET.get('page')

    p = Paginator(products, 20)
    try:
        products = p.page(page)
    except:
        products = p.page(1)

    context = {
        'title':'สต๊อก', 
        'products':products,
        'pending_orders_count': count_pending_orders(),}
    return render(request, 'stock.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def workgroup(request):
    workgroup = WorkGroup.objects.all()

    query = request.GET.get('q')
    if query is not None:
        lookups = Q(work_group__icontains=query)
        workgroup = WorkGroup.objects.filter(lookups)

    page = request.GET.get('page')

    p = Paginator(workgroup, 20)
    try:
        workgroup = p.page(page)
    except:
        workgroup = p.page(1)

    context = {
        'title':'กลุ่มงาน', 
        'workgroup':workgroup,
        'pending_orders_count': count_pending_orders(),}
    return render(request, 'workgroup.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def add_work_group(request):
    if request.method == 'POST':
        form = WorkGroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มหมวดหมู่เรียบร้อยแล้ว!')
            return redirect('dashboard:workgroup')  # เปลี่ยน 'success_page' เป็นชื่อ URL ของหน้าที่ต้องการไปหลังจากบันทึกข้อมูล
    else:
        form = WorkGroupForm()
    
    context = {'title':'เพิ่มกลุ่มงาน', 
               'form':form,
                'pending_orders_count': count_pending_orders(),}
    
    return render(request, 'add_work_group.html', context)


@user_passes_test(is_authorized_manager)
@login_required
def import_work_group(request):
    if request.method == 'POST':
        file = request.FILES['file']
        try:
            df = pd.read_excel(file)
            for index, row in df.iterrows():
                WorkGroup.objects.create(work_group=row['กลุ่มงาน'])
            
            messages.success(request, 'นำเข้าข้อมูลกลุ่มงานสำเร็จ')
        
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {e}')
        
    return redirect('dashboard:workgroup')  



@user_passes_test(is_authorized_manager)
@login_required
def delete_workgroup(request, id):
    workgroup = WorkGroup.objects.filter(id=id).delete()
    messages.success(request, 'ลบกลุ่มงานสำเร็จ')
    return redirect('dashboard:workgroup')



@user_passes_test(is_authorized_manager)
@login_required
def edit_workgroup(request, id):
    work= WorkGroup.objects.get(id=id)
    form = EditWorkGroupForm()

    if request.method == 'POST':
        form = EditWorkGroupForm(request.POST, request.FILES, instance=work)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขข้อมูลสำเร็จ')
            return redirect('dashboard:workgroup')
    else:
        form = EditWorkGroupForm(instance=work)
    context = {'title': 'แก้ไขข้อกลุ่มงาน', 
               'work':work,
               'form':form,
               'pending_orders_count': count_pending_orders(),}
    return render(request, 'edit_workgroup.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def category(request):
    category = Category.objects.all()

    query = request.GET.get('q')
    if query is not None:
        lookups = Q(name_cate__icontains=query)
        category = Category.objects.filter(lookups)

    page = request.GET.get('page')

    p = Paginator(category, 20)
    try:
        category = p.page(page)
    except:
        category = p.page(1)

    context = {
        'title':'หมวดหมู่หลัก', 
        'category':category,
        'pending_orders_count': count_pending_orders(),}
    return render(request, 'category.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def add_category(request):
    if request.method == 'POST':
        form = AddCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มหมวดหมู่เรียบร้อยแล้ว!')
            return redirect('dashboard:add_category')
    else:
        form = AddCategoryForm()
    context = {'title':'เพิ่มหมวดหมู่หลัก', 
               'form':form,
                'pending_orders_count': count_pending_orders(),}
    return render(request, 'add_category.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def delete_category(request, id):
    category = Category.objects.filter(id=id).delete()
    messages.success(request, 'ลบหมวดหมู่หลักสำเร็จ')
    return redirect('dashboard:category')



@user_passes_test(is_authorized_manager)
@login_required
def edit_category(request, id):
    cate= Category.objects.get(id=id)
    form = EditCategoryForm()

    if request.method == 'POST':
        form = EditCategoryForm(request.POST, request.FILES, instance=cate)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขข้อมูล สำเร็จ')
            return redirect('dashboard:category')
    else:
        form = EditCategoryForm(instance=cate)
    context = {'title': 'แก้ไขข้อมูลหมวดหมู่หลัก', 
               'cate':cate,
               'form':form,
               'pending_orders_count': count_pending_orders(),}
    return render(request, 'edit_category.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def subcategory(request):
    subcategory = Subcategory.objects.all()

    query = request.GET.get('q')
    if query is not None:
        lookups = Q(name_sub__icontains=query)|Q(category__name_cate__icontains=query)
        subcategory = Subcategory.objects.filter(lookups)

    page = request.GET.get('page')

    p = Paginator(subcategory, 20)
    try:
        subcategory = p.page(page)
    except:
        subcategory = p.page(1)

    context = {
        'title':'หมวดหมู่ย่อย', 
        'subcategory':subcategory,
        'pending_orders_count': count_pending_orders(),}
    return render(request, 'subcategory.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def add_subcategory(request):
    if request.method == 'POST':
        form = AddSubcategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มหมวดหมู่ย่อยเรียบร้อยแล้ว!')
            return redirect('dashboard:add_subcategory')
    else:
        form = AddSubcategoryForm()
    context = {'title':'เพิ่มหมวดหมู่ย่อย', 
               'form':form,
                'pending_orders_count': count_pending_orders(),}
    return render(request, 'add_subcategory.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def delete_subcategory(request, id):
    category = Subcategory.objects.filter(id=id).delete()
    messages.success(request, 'ลบหมวดหมู่ย่อยสำเร็จ')
    return redirect('dashboard:subcategory')



@user_passes_test(is_authorized_manager)
@login_required
def edit_subcategory(request, id):
    sub= Subcategory.objects.get(id=id)
    form = EditSubcategoryForm()

    if request.method == 'POST':
        form = EditSubcategoryForm(request.POST, request.FILES, instance=sub)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขข้อมูล สำเร็จ')
            return redirect('dashboard:subcategory')
    else:
        form = EditSubcategoryForm(instance=sub)
    context = {'title': 'แก้ไขข้อมูลหมวดหมู่ย่อย', 
               'sub':sub,
               'form':form,
               'pending_orders_count': count_pending_orders(),}
    return render(request, 'edit_subcategory.html', context)



@user_passes_test(is_authorized_manager)
@login_required
def orders_all(request):
    orders_all = Order.objects.all()

    query = request.GET.get('q')
    if query is not None:
        lookups = Q(id__icontains=query)
        orders_all = Order.objects.filter(lookups)

    page = request.GET.get('page')
    p = Paginator(orders_all, 20)
    try:
        orders_all = p.page(page)
    except:
        orders_all = p.page(1)

    context = {
        'title':'คำร้องเบิกวัสดุทั้งหมด', 
        'orders_all':orders_all,
        'pending_orders_count': count_pending_orders(),
        }
    return render(request, 'orders_all.html', context)


@user_passes_test(is_authorized_manager)
@login_required
def orders(request):
    orders = Order.objects.all()

    query = request.GET.get('q')
    if query is not None:
        lookups = Q(id__icontains=query)|Q(date_created__icontains=query)
        orders = Order.objects.filter(lookups).order_by('id')

    page = request.GET.get('page')
    p = Paginator(orders, 20)
    try:
        orders = p.page(page)
    except:
        orders = p.page(1)

    # ดึงข้อมูลออร์เดอร์ทั้งหมดที่รอการยืนยัน
    orders_waiting_status = Order.objects.filter(status=None).order_by('id')

    # ส่งข้อมูล approval_count ไปยัง template
    context = {
        'title':'คำร้องใหม่',
        'orders':'orders',
        'orders':orders_waiting_status,
        'status_count': orders_waiting_status.count(),
        'pending_orders_count': count_pending_orders(),
        }
    return render(request, 'orders.html', context)


# ใหม่4
# orders/views.py
@user_passes_test(is_authorized_manager)
@login_required
def approve_orders(request, order_id):
    ap = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        form = ApproveForm(request.POST, instance=ap)
        if form.is_valid():
            old_status = ap.status  # เก็บสถานะเดิมก่อนการเปลี่ยนแปลง
            new_status = form.cleaned_data.get('status')
            if new_status == False:
                print("Order is being rejected, restoring stock...")
                # คืนจำนวนสินค้ากลับไปยังสต๊อก
                for item in ap.items.all():
                    product = item.product
                    product.quantityinstock += item.quantity
                    product.save()
                    print(f"Restored {item.quantity} of {product.product_name} to stock.")

                    # คืนจำนวนสินค้าที่รับเข้าใน Receiving
                    receiving = item.receiving
                    receiving.quantity += item.quantity
                    receiving.save()
                    print(f"Restored {item.quantity} to receiving ID {receiving.id}.")
            form.save()
            messages.success(request, 'ดำเนินการสำเร็จ')

            # Notify the user about the approval
            notify_user_approved(ap.id)
            
            return redirect(reverse('dashboard:order_detail', args=[order_id]))
        else:
            messages.error(request, 'ดำเนินการไม่สำเร็จ')
    else:
        form = ApproveForm(instance=ap)
        
    return render(request, 'orders.html', {
        'ap': ap,
        'form': form,
        'title': 'แก้ไขข้อมูลสมาชิก',
        'pending_orders_count': count_pending_orders(),
    })


@user_passes_test(is_authorized_manager)
@login_required
def order_detail(request, id):
    order = Order.objects.filter(id=id).first()
    items = Issuing.objects.filter(order=order).all()
    context = {
        'title':'รายการเบิกจ่ายวัสดุ', 
        'items':items, 
        'order':order,
        'pending_orders_count': count_pending_orders(),
        }
    return render(request, 'order_detail.html', context)


