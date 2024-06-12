from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.core.paginator import Paginator
from app_linebot.views import notify_user_approved
from django.db.models import Q, Sum, Max, F, ExpressionWrapper, DecimalField
from shop.models import Category, Product, Stock, Subcategory, Suppliers, Total_Quantity, TotalQuantity, Receiving
from accounts.models import MyUser, Profile
from orders.models import Order, Issuing
from .forms import AddProductForm, AddCategoryForm, AddReceivingForm, AddSubcategoryForm, EditCategoryForm, EditProductForm, ApproveForm, AddSuppliersForm, EditSubcategoryForm, EditSuppliersForm, ReceivingForm
from django.db.models import F
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime, timedelta
import openpyxl, re
from django.http import HttpResponse
from collections import defaultdict
import calendar
import locale
locale.setlocale(locale.LC_TIME, 'th_TH.UTF-8')  # ตั้งค่า locale เป็นภาษาไทย

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


from django.http import Http404

def is_manager(user):
    if not user.is_manager:
        raise Http404
    return True

def is_executive(user):
    if not user.is_executive:
        raise Http404
    return True

def is_admin(user):
    if not user.is_admin:
        raise Http404
    return True

def is_authorized(user):
    try:
        return is_manager(user) and is_executive(user) and is_admin(user)
    except Http404:
        return False
    



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
        total_issued_value = issued_items.aggregate(total_cost=Sum(F('price') * F('quantity')))['total_cost'] or 0

        user_issuings = defaultdict(int)
        for issuing in issued_items:
            user_full_name = issuing.order.user.get_first_name()
            user_issuings[user_full_name] += issuing.quantity
            all_users.add(user_full_name)

        report_data.append({
            'product': product.product_name,
            'unit': product.unit,
            'previous_balance': previous_balance,
            'total_balance': total_balance,
            **user_issuings,
            'issued_current_month': issued_current_month,
            'remaining_balance': remaining_balance,
            'total_issued_value': total_issued_value,
            'note': '',
        })

    # Create a new Excel workbook and worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    # Add header rows to the worksheet
    header_rows = [
        ['รายการเบิกวัสดุ'],
        ['ประจำเดือน', f'{month} พ.ศ. {year} ประจำปีงบประมาณ พ.ศ. 2567'],
        ['หน่วยงาน โครงการอุทยานวิทยาศาสตร์ มหาวิทยาลัยอุบลราชธานี']
    ]

    for header_row in header_rows:
        worksheet.append(header_row)

    # Add column headers to the worksheet
    headers = ['ลำดับ', 'รายการสินค้า', 'หน่วยนับ', 'จำนวนคงเหลือ (ยกมา)', 'รวมจำนวนคงเหลือ'] + list(all_users) + ['รวมจำนวนที่เบิก', 'จำนวนคงเหลือทั้งหมด (หักจากที่เบิก)', 'มูลค่าสินค้าเบิกทั้งสิ้น (บาท)', 'หมายเหตุ']
    worksheet.append(headers)

    # Loop through to add data to the worksheet
    for index, item in enumerate(report_data, start=1):
        row = [
            index,  # เปลี่ยน item['forloop.counter'] เป็น index
            item['product'],
            item['unit'],
            item['previous_balance'],
            item['total_balance'],
            *[item.get(user, 0) for user in sorted(all_users)],
            item['issued_current_month'],
            item['remaining_balance'],
            item['total_issued_value'],
            item['note']
        ]
        worksheet.append(row)

    # Create an HttpResponse for the Excel file and save the workbook into the response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=monthly_report_{}_{}.xlsx'.format(month, year)
    workbook.save(response)

    # Return the response
    return response




# รายงาน4 ทำคอลัมน์ผู้ใช้งานได้แล้ว
def monthly_report(request, month=None, year=None):
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

    # Get Thai month name
    month_name = thai_month_name(month)

    # ในฟังก์ชัน monthly_report
    buddhist_year = convert_to_buddhist_era(year)

    start_date = datetime(year, month, 1)
    end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)

    previous_month_start = (start_date - timedelta(days=1)).replace(day=1)
    previous_month_end = start_date - timedelta(seconds=1)

    products = Product.objects.all()

    report_data = []
    all_users = set()

    for product in products:
        # คำนวณจำนวนคงเหลือยกมา
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
        total_issued_value = issued_items.aggregate(total_cost=Sum(F('price') * F('quantity')))['total_cost'] or 0

        user_issuings = defaultdict(int)
        for issuing in issued_items:
            user_full_name = issuing.order.user.get_first_name()
            user_issuings[user_full_name] += issuing.quantity
            all_users.add(user_full_name)

        report_data.append({
            'product': product.product_name,
            'unit': product.unit,
            'previous_balance': previous_balance,
            'total_balance': total_balance,
            'user_issuings': user_issuings,
            'issued_current_month': issued_current_month,
            'remaining_balance': remaining_balance,
            'total_issued_value': total_issued_value,
            'note': '',
        })

    context = {
        'title': 'รายงานประจำเดือน',
        'report_data': report_data,
        'all_users': sorted(all_users),
        'month': month,
        'year': year,
        'now': now,
        'years': range(2020, now.year + 1),
        'months': [
            (1, 'มกราคม'), (2, 'กุมภาพันธ์'), (3, 'มีนาคม'), (4, 'เมษายน'),
            (5, 'พฤษภาคม'), (6, 'มิถุนายน'), (7, 'กรกฎาคม'), (8, 'สิงหาคม'),
            (9, 'กันยายน'), (10, 'ตุลาคม'), (11, 'พฤศจิกายน'), (12, 'ธันวาคม')
        ],  # ลิสต์ของเดือน
        
        'pending_orders_count': count_pending_orders(),
        'month_name': month_name,  # Pass month_name variable to template
        'buddhist_year':buddhist_year,
    }

    return render(request, 'monthly_report.html', context)







# @user_passes_test(is_authorized)
@login_required
def dashboard_home(request):
    context = {'title':'dashboard' ,
               'products':products ,
                'pending_orders_count': count_pending_orders(),
               }
    return render(request, 'dashboard_home.html', context)


@user_passes_test(is_manager)
@login_required
def products(request):
    query = request.GET.get('q')
    products = Product.objects.all()

    # products_with_quantities = []
    # for product in products:
    #     total_quantity = Receiving.objects.filter(product=product).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    #     product.total_quantity = total_quantity
    #     products_with_quantities.append(product)

    if query is not None:
        lookups = Q(product_id__icontains=query) | Q(product_name__icontains=query)
        products = Product.objects.filter(lookups)

    # products = products.annotate(total_quantity_received=Sum('Receiving__quantity'))
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


@user_passes_test(is_manager)
@login_required
def add_product(request):
    if request.method == 'POST':
        form = AddProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มวัสดุเรียบร้อยแล้ว!')
            return redirect('dashboard:add_product')
    else:
        form = AddProductForm()
    context = {'title':'เพิ่มวัสดุ', 'form':form,
                'pending_orders_count': count_pending_orders(),}
    return render(request, 'add_product.html', context)

@user_passes_test(is_manager)
@login_required
def delete_product(request, id):
    product = Product.objects.filter(id=id).delete()
    messages.success(request, 'ลบวัสดุสำเร็จ')
    return redirect('dashboard:products')

@user_passes_test(is_manager)
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



@user_passes_test(is_manager)
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


@user_passes_test(is_manager)
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


@user_passes_test(is_manager)
@login_required
def delete_suppliers(request, id):
    suppliers = Suppliers.objects.filter(id=id).delete()
    messages.success(request, 'ลบซัพพลายเออร์สำเร็จ')
    return redirect('dashboard:supplierss')


@user_passes_test(is_manager)
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


@user_passes_test(is_manager)
@login_required
def detail_suppliers(request, id):
    sup = get_object_or_404(Suppliers, id=id)
    context = {
        'title':'รายละเอียดซัพพลายเออร์', 
        'sup':sup,
        'pending_orders_count': count_pending_orders(),
        }
    return render(request, 'detail_suppliers.html', context)




@user_passes_test(is_manager)
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


@user_passes_test(is_manager)
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
            # Product.objects.filter(id=product.id).update(quantityinstock=F('quantityinstock') + received_product.quantity)

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




def update_received_product(request, id):
    received_product = get_object_or_404(Receiving, id=id)

    if request.method == 'POST':
        form = ReceivingForm(request.POST, instance=received_product)
        if form.is_valid():
            updated_received_product = form.save(commit=False)
            updated_received_product.save()

            # อัพเดทจำนวนสินค้าในสต็อก
            product = updated_received_product.product
            stock, created = Stock.objects.get_or_create(product=product)
            stock.quantity -= received_product.quantityreceived  # ลบจำนวนเดิม
            stock.quantity += updated_received_product.quantity  # เพิ่มจำนวนใหม่
            stock.save()

            # อัพเดทจำนวนทั้งหมดที่รับเข้า
            total, created = Total_Quantity.objects.get_or_create(product=product)
            total.totalquantity -= received_product.quantityreceived  # ลบจำนวนเดิม
            total.totalquantity += updated_received_product.quantityreceived  # เพิ่มจำนวนใหม่
            total.save()

            # อัปเดตจำนวนสินค้าในตาราง Product
            # Product.objects.filter(id=product.id).update(quantityinstock=F('quantityinstock') + received_product.quantity)

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



@user_passes_test(is_manager)
@login_required
def delete_receive(request, id):
    suppliers = Receiving.objects.filter(id=id).delete()
    messages.success(request, 'ลบรับเข้าสำเร็จ')
    return redirect('dashboard:receive_list')



@user_passes_test(is_manager)
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




@user_passes_test(is_manager)
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




@user_passes_test(is_manager)
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


@user_passes_test(is_manager)
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


@user_passes_test(is_manager)
@login_required
def delete_category(request, id):
    category = Category.objects.filter(id=id).delete()
    messages.success(request, 'ลบหมวดหมู่หลักสำเร็จ')
    return redirect('dashboard:category')


@user_passes_test(is_manager)
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




@user_passes_test(is_manager)
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


@user_passes_test(is_manager)
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


@user_passes_test(is_manager)
@login_required
def delete_subcategory(request, id):
    category = Subcategory.objects.filter(id=id).delete()
    messages.success(request, 'ลบหมวดหมู่ย่อยสำเร็จ')
    return redirect('dashboard:subcategory')


@user_passes_test(is_manager)
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


@user_passes_test(is_manager)
@login_required
def orders_all(request):
    orders_all = Order.objects.all()

    query = request.GET.get('q')
    if query is not None:
        lookups = Q(id__icontains=query)|Q(date_created__icontains=query)
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



@user_passes_test(is_manager)
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
