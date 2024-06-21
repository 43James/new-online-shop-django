from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
# from dashboard.views import products

from dashboard.views import count_pending_orders
from shop.models import MonthlyStockRecord, Product, Category, Receiving, Stock, Subcategory
from django.db.models import Q
from cart.forms import QuantityForm
from .filters import FilterProduct, FilterSubcategory
from datetime import datetime, timedelta
from django.db.models import F



def paginat(request, list_objects):
	p = Paginator(list_objects, 20)
	page_number = request.GET.get('page')
	try:
		page_obj = p.get_page(page_number)
	except PageNotAnInteger:
		page_obj = p.page(1)
	except EmptyPage:
		page_obj = p.page(p.num_pages)
	return page_obj


# ในกรณีใช้กับตาราง Product

@login_required
def home_page(request):
    products = Product.objects.all()
    
    # คำนวณ total_quantity สำหรับแต่ละสินค้า
    for product in products:
        product.total_quantity = Receiving.total_quantity_by_product(product.id)
    
    context = {'products': paginat(request, products),}
    return render(request, 'home_page.html', context)



@login_required
def product_detail(request, slug):
	form = QuantityForm()
	product = get_object_or_404(Product, slug=slug)
	related_products = Product.objects.filter(category=product.category).all()[:5]
	total_quantity = Receiving.total_quantity_by_product(product.id)
	context = {
		'product_name':product.product_name,
		'product':product,
		'form':form,
		'favorites':'favorites',
		'related_products':related_products,
		'stock': Stock.objects.all(),
		'total_quantity':total_quantity
	}
	if request.user.likes.filter(id=product.id).first():
		context['favorites'] = 'remove'
	return render(request, 'product_detail.html', context)



@login_required
def add_to_favorites(request, product_id):
	product = get_object_or_404(Product, id=product_id)
	request.user.likes.add(product)
	return redirect('shop:product_detail', slug=product.slug)


@login_required
def remove_from_favorites(request, product_id):
	product = get_object_or_404(Product, id=product_id)
	request.user.likes.remove(product)
	return redirect('shop:favorites')


@login_required
def favorites(request):
	products = request.user.likes.all()

	# คำนวณ total_quantity สำหรับแต่ละสินค้า
	for product in products:
		product.total_quantity = Receiving.total_quantity_by_product(product.id)

	context = {'title':'Favorites', 'products':products}
	return render(request, 'favorites.html', context)


@login_required
def search(request):
	query = request.GET.get('q')
	products = Product.objects.filter(title__icontains=query).all()
	context = {'products': paginat(request ,products)}
	return render(request, 'home_page.html', context)


@login_required
def filter_by_category(request, category_id=None, subcategory_id=None):
    categories = Category.objects.all()

    if category_id:
        category = get_object_or_404(Category, pk=category_id)
        subcategories = Subcategory.objects.filter(category=category)
    else:
        category = None
        subcategories = None

    if subcategory_id:
        subcategory = get_object_or_404(Subcategory, pk=subcategory_id)
        products = Product.objects.filter(category=subcategory)
    else:
        subcategory = None
        products = Product.objects.all()

	# คำนวณ total_quantity สำหรับแต่ละสินค้า
    for product in products:
        product.total_quantity = Receiving.total_quantity_by_product(product.id)

    context = {
        'categories': categories,
        'selected_category': category,
        'subcategories': subcategories,
        'selected_subcategory': subcategory,
        'products': products,
    }

    return render(request, 'home_page.html', context)


# def record_monthly_stock():
#     now = datetime.now()
#     first_day_of_current_month = now.replace(day=1)
#     last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)

#     # Get all products
#     products = Product.objects.all()

#     for product in products:
#         # Save the end of month balance for each product
#         MonthlyStockRecord.objects.create(
#             product=product,
#             month=last_day_of_previous_month.month,
#             year=last_day_of_previous_month.year,
#             end_of_month_balance=product.quantityinstock
#         )

#     print("Monthly stock record created successfully")



# def record_monthly_stock_view(request):
#     if request.method == 'POST':
#         form = RecordMonthlyStockForm(request.POST)
#         if form.is_valid() and form.cleaned_data['confirm']:
#             # now = timezone.now()
#             now = datetime.now()
#             first_day_of_current_month = now.replace(day=1)
#             last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)

#             products = Product.objects.all()
#             for product in products:
#                 MonthlyStockRecord.objects.create(
#                     product=product,
#                     month=last_day_of_previous_month.month,
#                     year=last_day_of_previous_month.year,
#                     end_of_month_balance=product.quantityinstock
#                 )

#             print("Monthly stock record created successfully")
#             return redirect('shop:record_monthly_stock')  # เปลี่ยนเป็นชื่อ URL ของหน้า success page ของคุณ
#     else:
#         form = RecordMonthlyStockForm()

#     return render(request, 'record_monthly_stock.html', {'form': form})



# def monthly_stock_records(request):
#     now = datetime.now()
#     last_month = now.month - 1 if now.month > 1 else 12
#     last_year = now.year if now.month > 1 else now.year - 1

#     # ตรวจสอบว่ามีการระบุเดือนและปีในพารามิเตอร์ GET หรือไม่ ถ้าไม่มีใช้เดือนและปีของเดือนที่แล้ว
#     month = int(request.GET.get('month', last_month))
#     year = int(request.GET.get('year', last_year))

#     # กรองข้อมูล MonthlyStockRecord ตามเดือนและปี
#     records = MonthlyStockRecord.objects.filter(month=month, year=year)

#     # กำหนดค่าให้กับตัวแปร context
#     context = {
#         'title': 'ข้อมูลวัสดุประจำเดือน (ยกมา)',
#         'records': records,
#         'selected_month': month,
#         'selected_year': year,
#         'years': range(2020, datetime.now().year + 1),
#         'months': [
#             (1, 'มกราคม'), (2, 'กุมภาพันธ์'), (3, 'มีนาคม'), (4, 'เมษายน'),
#             (5, 'พฤษภาคม'), (6, 'มิถุนายน'), (7, 'กรกฎาคม'), (8, 'สิงหาคม'),
#             (9, 'กันยายน'), (10, 'ตุลาคม'), (11, 'พฤศจิกายน'), (12, 'ธันวาคม')
#         ],
#         'pending_orders_count': count_pending_orders(),

#     }
#     previous_month = month - 1 if month > 1 else 12
#     previous_year = year if month > 1 else year - 1
#     context['previous_month_name'] = context['months'][previous_month][1]
#     context['previous_year_buddhist'] = previous_year + 543

#     return render(request, 'monthly_stock_records.html', context)