from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from dashboard.views import count_pending_orders
from orders.models import Order
from shop.models import MonthlyStockRecord, Product, Category, Receiving, Stock, Subcategory
from cart.forms import QuantityForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


from django.core.exceptions import PermissionDenied

def is_general(user):
    if not user.is_general:
        raise PermissionDenied
    return True

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
    if user.is_manager or user.is_warehouse_manager or user.is_executive or user.is_admin:
        return True
    raise PermissionDenied

def is_authorized_admin(user):
    if is_admin(user):
        return True
    raise PermissionDenied

# def is_authorized_manager(user, request):
#     if user.is_manager or user.is_admin:
#         return True
#     return render(request, '403.html', status=403)
    

# def some_view(request):
#     return render(request, '403.html', context={})

# def custom_404_view(request, exception=None):
#     return render(request, '404.html', status=404)

def paginat(request, list_objects):
	p = Paginator(list_objects, 18)
	page_number = request.GET.get('page')
	try:
		page_obj = p.get_page(page_number)
	except PageNotAnInteger:
		page_obj = p.page(1)
	except EmptyPage:
		page_obj = p.page(p.num_pages)
	return page_obj


def count_unconfirmed_orders(user):
    # ดึงข้อมูลออเดอร์ทั้งหมดที่รอการยืนยัน
    pending_orders = Order.objects.filter(user=user, status=True, confirm=False)
    return pending_orders.count()


# ในกรณีใช้กับตาราง Product
@user_passes_test(is_general)
@login_required
# def home_page(request):
#     products = Product.objects.all()
    
#     # คำนวณ total_quantity สำหรับแต่ละสินค้า
#     for product in products:
#         product.total_quantity = Receiving.total_quantity_by_product(product.id)
    
#     context = {'products': paginat(request, products),}
#     return render(request, 'home_page.html', context)

# @login_required
# def home_page(request):
#     # ดึงเฉพาะสินค้าที่มีในสต็อก (total_quantity > 0)
#     products = Product.objects.all()

#     # คำนวณ total_quantity สำหรับแต่ละสินค้า
#     available_products = []
#     for product in products:
#         product.total_quantity = Receiving.total_quantity_by_product(product.id)
#         if product.total_quantity > 0:
#             available_products.append(product)

#     context = {'products': paginat(request, available_products)}
#     return render(request, 'home_page.html', context)

@login_required
def home_page(request):
    # ดึงข้อมูลสินค้าทั้งหมด
    products = Product.objects.all().order_by('product_name')

    query = request.GET.get('q')
    if query is not None:
        lookups = Q(product_name__icontains=query) | Q(product_id__icontains=query)
        products = Product.objects.filter(lookups).order_by('product_name')

    # แยกวัสดุที่มีในสต็อกและวัสดุที่ไม่มีในสต็อก
    in_stock_products = []
    out_of_stock_products = []

    # คำนวณ total_quantity สำหรับแต่ละสินค้า
    for product in products:
        product.total_quantity = Receiving.total_quantity_by_product(product.id)
        if product.total_quantity > 0:
            in_stock_products.append(product)  # วัสดุที่มีในสต็อก
        else:
            out_of_stock_products.append(product)  # วัสดุที่ไม่มีในสต็อก

    # รวมวัสดุที่มีในสต็อกไว้ข้างบนและที่ไม่มีในสต็อกไว้ท้าย ๆ
    sorted_products = in_stock_products + out_of_stock_products

    # ตรวจสอบออเดอร์ที่ยังไม่ยืนยันรับวัสดุ
    # unconfirmed_orders = Order.objects.filter(user=request.user, status=True, pay_item=True, confirm=False)
    # if unconfirmed_orders.exists():
    #     messages.info(request, "คุณมีออเดอร์ที่ยังไม่ยืนยันรับวัสดุ กรุณายืนยันรับวัสดุ")

    unconfirmed_count = count_unconfirmed_orders(request.user)  # เปลี่ยนชื่อเพื่อหลีกเลี่ยงความสับสน


    # ตรวจสอบออเดอร์ที่ยังไม่ยืนยันรับวัสดุ
    unconfirmed_orders = Order.objects.filter(user=request.user, status=True, pay_item=True, confirm=False)
    
    # นับจำนวนออเดอร์ที่รอการยืนยัน
    count_unconfirmed = unconfirmed_orders.count()
    
    if count_unconfirmed > 0:
        messages.info(request, f"คุณมีออเดอร์ที่ยังไม่ยืนยันรับวัสดุ: {count_unconfirmed} รายการ กรุณายืนยันรับวัสดุ")

    # ส่งผลลัพธ์ไปยัง template
    context = {'products': paginat(request, sorted_products),
               'count_unconfirmed_orders': unconfirmed_count,
               }
    return render(request, 'home_page.html', context)




@user_passes_test(is_general)
@login_required
# def product_detail(request, slug):
# 	form = QuantityForm()
# 	product = get_object_or_404(Product, slug=slug)
# 	related_products = Product.objects.filter(category=product.category).all()[:5]
# 	total_quantity = Receiving.total_quantity_by_product(product.id)
# 	context = {
# 		'product_name':product.product_name,
# 		'product':product,
# 		'form':form,
# 		'favorites':'favorites',
# 		'related_products':related_products,
# 		'stock': Stock.objects.all(),
# 		'total_quantity':total_quantity
# 	}
# 	if request.user.likes.filter(id=product.id).first():
# 		context['favorites'] = 'remove'
# 	return render(request, 'product_detail.html', context)


def product_detail(request, product_id):
    form = QuantityForm()
    product = get_object_or_404(Product, product_id=product_id)
    related_products = Product.objects.filter(category=product.category).all()[:5]
    total_quantity = Receiving.total_quantity_by_product(product.id)
     
    # เรียกใช้ฟังก์ชันนับจำนวนออเดอร์ที่รอการยืนยัน
    unconfirmed_count = count_unconfirmed_orders(request.user)  # เปลี่ยนชื่อเพื่อหลีกเลี่ยงความสับสน

    context = {
        'product_name': product.product_name,
        'product': product,
        'form': form,
        'related_products': related_products,
        'stock': Stock.objects.all(),
        'total_quantity': total_quantity,
        'count_unconfirmed_orders': unconfirmed_count,  # ใช้ตัวแปรที่มีชื่อไม่ซ้ำ
    }

    # ตรวจสอบว่าผู้ใช้ได้เพิ่มสินค้านี้ลงในรายการโปรดหรือไม่
    if request.user.likes.filter(id=product.id).exists():
        context['favorites'] = 'remove'  # ถ้าสินค้าอยู่ในรายการโปรด
    else:
        context['favorites'] = 'favorites'  # ถ้าไม่อยู่ในรายการโปรด

    return render(request, 'product_detail.html', context)



@user_passes_test(is_general)
@login_required
def add_to_favorites(request, product_id):
	product = get_object_or_404(Product, id=product_id)
	request.user.likes.add(product)
	return redirect('shop:product_detail', product_id=product.product_id)


@user_passes_test(is_general)
@login_required
def remove_from_favorites(request, product_id):
	product = get_object_or_404(Product, id=product_id)
	request.user.likes.remove(product)
	return redirect('shop:favorites')


@user_passes_test(is_general)
@login_required
def favorites(request):
    # ดึงสินค้าที่ผู้ใช้ชอบทั้งหมด
    products = request.user.likes.all()

    # คำนวณ total_quantity สำหรับแต่ละสินค้า
    for product in products:
        product.total_quantity = Receiving.total_quantity_by_product(product.id)

    # เรียกใช้ฟังก์ชัน count_unconfirmed_orders
    count_unconfirmed = count_unconfirmed_orders(request.user)

    context = {
        'title': 'Favorites',
        'products': products,
        'count_unconfirmed_orders': count_unconfirmed,  # ส่งผลลัพธ์ของฟังก์ชันไปยัง context
    }

    return render(request, 'favorites.html', context)


@user_passes_test(is_general)
@login_required
def search(request):
	query = request.GET.get('q')
	products = Product.objects.filter(title__icontains=query).all()
	context = {'products': paginat(request ,products)}
	return render(request, 'home_page.html', context)



@user_passes_test(is_general)
@login_required
def filter_by_category(request, category_id=None, subcategory_id=None):
    categories = Category.objects.all()
    count_unconfirmed = count_unconfirmed_orders(request.user)

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
        'count_unconfirmed_orders': count_unconfirmed,
    }

    return render(request, 'home_page.html', context)

