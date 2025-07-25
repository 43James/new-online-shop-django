from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from cart.utils.cart import Cart
from shop.views import count_unconfirmed_orders
from .forms import QuantityForm
from shop.models import Product, Receiving
from django.db import transaction  # import transaction
from django.contrib.auth.decorators import user_passes_test


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

# def auto_clear_cart(request):
#     if not request.session.get('cart_cleared'):  # ✅ ยังไม่เคลียร์
#         cart = Cart(request)
#         cart.logout()
#         request.session['cart_cleared'] = True   # ✅ Mark ว่าเคลียร์แล้ว
#         return JsonResponse({'success': True})
#     return JsonResponse({'success': False, 'message': 'already cleared'})

def auto_clear_cart(request):
    cart = request.session.get('cart', {})
    cleared = request.session.get('cart_cleared', False)

    if cleared:
        return JsonResponse({'success': False, 'message': 'already cleared'})

    for item_id, item in cart.items():
        added_time_str = item.get('added_time')
        if added_time_str:
            added_time = timezone.datetime.fromisoformat(added_time_str)
            if timezone.now() - added_time > timedelta(minutes=2):
                # คืนจำนวน stock ไปยังฐานข้อมูล
                product = Product.objects.get(id=item_id)
                product.stock += item['quantity']
                product.save()

    # ล้าง cart
    request.session['cart'] = {}
    request.session['cart_cleared'] = True  # ✅ ป้องกันการคืนซ้ำ
    request.session.modified = True

    return JsonResponse({'success': True})

# ใหม่2
@user_passes_test(is_authorized)
@login_required
def add_to_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = QuantityForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        quantity_to_add = data['quantity']
        note = request.POST.get('note', '')  # รับค่า note จาก POST data
        
        receivings = Receiving.objects.filter(product=product, quantity__gt=0).order_by('date_created')
        total_receiving_quantity = sum(receiving.quantity for receiving in receivings)
        if quantity_to_add > total_receiving_quantity:
            messages.error(request, 'จำนวนสินค้าในสต็อกไม่เพียงพอ!')
        else:
            cart.add(product=product, quantity=quantity_to_add, note=note)
            messages.success(request, 'เพิ่มลงในรถเข็น!')
    else:
        messages.error(request, 'กรุณาเพิ่มสินค้าลงในรถเข็น!')
    return redirect('shop:product_detail', product_id=product.product_id)



@user_passes_test(is_authorized)
@login_required
def show_cart(request):
    cart = Cart(request)
    count_unconfirmed = count_unconfirmed_orders(request.user)  # เรียกใช้ฟังก์ชันนับจำนวนออเดอร์ที่ยังไม่ยืนยัน

    context = {
        'title': 'Cart',
        'cart': cart,
        'count_unconfirmed_orders': count_unconfirmed,  # ส่งจำนวนออเดอร์ที่ยังไม่ยืนยันไปยัง context
    }

    return render(request, 'cart.html', context)




# ใหม่7
@user_passes_test(is_authorized)
@login_required
def remove_from_cart(request, product_id, receiving_id):
    cart = Cart(request)  # สร้าง instance ของ Cart
    product = get_object_or_404(Product, id=product_id)

    removed_item = cart.remove(product, receiving_id)  # ลบสินค้าด้วย receiving_id

    if removed_item:
        with transaction.atomic():
            product.quantityinstock += removed_item['quantity']
            product.save() # กรณีปิดไว้ไม่คืนจำนวนกลับไปยังสต๊อกในโปรดั๊กแล้ว

            receiving = Receiving.objects.get(id=removed_item['receiving_id'])
            receiving.quantity += removed_item['quantity']
            receiving.save()

        return redirect('cart:show_cart')
    else:
        messages.error(request, 'ไม่พบสินค้าในตะกร้า')
        return redirect('cart:show_cart')


