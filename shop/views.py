from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test
from dashboard.views import count_pending_orders
from shop.models import MonthlyStockRecord, Product, Category, Receiving, Stock, Subcategory
from cart.forms import QuantityForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


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
        return True
    

def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)


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


# ในกรณีใช้กับตาราง Product
@user_passes_test(is_authorized)
@login_required
def home_page(request):
    products = Product.objects.all()
    
    # คำนวณ total_quantity สำหรับแต่ละสินค้า
    for product in products:
        product.total_quantity = Receiving.total_quantity_by_product(product.id)
    
    context = {'products': paginat(request, products),}
    return render(request, 'home_page.html', context)


@user_passes_test(is_authorized)
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


@user_passes_test(is_authorized)
@login_required
def add_to_favorites(request, product_id):
	product = get_object_or_404(Product, id=product_id)
	request.user.likes.add(product)
	return redirect('shop:product_detail', slug=product.slug)


@user_passes_test(is_authorized)
@login_required
def remove_from_favorites(request, product_id):
	product = get_object_or_404(Product, id=product_id)
	request.user.likes.remove(product)
	return redirect('shop:favorites')


@user_passes_test(is_authorized)
@login_required
def favorites(request):
	products = request.user.likes.all()

	# คำนวณ total_quantity สำหรับแต่ละสินค้า
	for product in products:
		product.total_quantity = Receiving.total_quantity_by_product(product.id)

	context = {'title':'Favorites', 'products':products}
	return render(request, 'favorites.html', context)


@user_passes_test(is_authorized)
@login_required
def search(request):
	query = request.GET.get('q')
	products = Product.objects.filter(title__icontains=query).all()
	context = {'products': paginat(request ,products)}
	return render(request, 'home_page.html', context)



@user_passes_test(is_authorized)
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

