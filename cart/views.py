from datetime import timedelta, timezone
from django.http import Http404, JsonResponse
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

# auto_clear_cart ของ Product & Receiving
# def auto_clear_cart(request):
#     cart = request.session.get('cart', {})
#     cleared = request.session.get('cart_cleared', False)

#     if cleared:
#         return JsonResponse({'success': False, 'message': 'already cleared'})

#     for item_id, item in cart.items():
#         added_time_str = item.get('added_time')
#         if added_time_str:
#             added_time = timezone.datetime.fromisoformat(added_time_str)
#             if timezone.now() - added_time > timedelta(minutes=2):
#                 # คืนจำนวน stock ไปยังฐานข้อมูล
#                 product = Product.objects.get(id=item_id)
#                 product.stock += item['quantity']
#                 product.save()

#     # ล้าง cart
#     request.session['cart'] = {}
#     request.session['cart_cleared'] = True  # ✅ ป้องกันการคืนซ้ำ
#     request.session.modified = True

#     return JsonResponse({'success': True})

def auto_clear_cart(request):
    """
    ตรวจสอบและลบรายการในรถเข็นที่หมดอายุ (เกิน 5 นาที) 
    พร้อมคืนสต็อกที่ถูกจองไว้ไปยังตาราง Receiving โดยอัตโนมัติ
    """
    
    # 1. สร้าง Cart instance
    cart_instance = Cart(request)
    
    # 2. เรียกใช้เมธอด __iter__ เพื่อ trigger logic การตรวจสอบและลบรายการที่หมดอายุ
    # การวนซ้ำนี้จะทำให้โค้ดใน __iter__ ทำงาน รวมถึงการเรียก cart.remove()
    # ซึ่งจะคืนสต็อกไปที่ Receiving ตามที่ได้แก้ไขไว้
    
    # เราไม่จำเป็นต้องเก็บผลลัพธ์ แต่ต้องวนซ้ำให้จบ
    for item in cart_instance:
        pass 
    
    # 3. ตอบกลับ
    return JsonResponse({
        'success': True, 
        'message': 'Expired items checked and removed. Stock restored to Receiving.'
    })


# add_to_cart ของ Product & Receiving
@user_passes_test(is_authorized)
@login_required
def add_to_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = QuantityForm(request.POST)

    if form.is_valid():
        data = form.cleaned_data
        quantity_to_add = data['quantity']
        note = request.POST.get('note', '')

        receivings = Receiving.objects.filter(product=product, quantity__gt=0).order_by('date_created')
        total_receiving_quantity = sum(receiving.quantity for receiving in receivings)

        if quantity_to_add > total_receiving_quantity:
            messages.error(request, 'จำนวนสินค้าในสต็อกไม่เพียงพอ!')
        else:
            success = cart.add(product=product, quantity=quantity_to_add, note=note)
            if success:
                messages.success(request, 'เพิ่มลงในรถเข็นแล้ว!')
            # ไม่ต้อง else เพราะข้อความ error ถูกแสดงจากใน cart.add แล้ว
    else:
        messages.error(request, 'กรุณาเพิ่มสินค้าลงในรถเข็น!')

    return redirect('shop:product_detail', product_id=product.product_id)

# show_cart ของ Product & Receiving
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


# aremove_from_cart ของ Product & Receiving
# @user_passes_test(is_authorized)
# @login_required
# def remove_from_cart(request, product_id, receiving_id):
#     cart = Cart(request)  # สร้าง instance ของ Cart
#     product = get_object_or_404(Product, id=product_id)

#     removed_item = cart.remove(product, receiving_id)  # ลบสินค้าด้วย receiving_id

#     if removed_item:
#         with transaction.atomic():
#             product.quantityinstock += removed_item['quantity']
#             product.save() # กรณีปิดไว้ไม่คืนจำนวนกลับไปยังสต๊อกในโปรดั๊กแล้ว

#             receiving = Receiving.objects.get(id=removed_item['receiving_id'])
#             receiving.quantity += removed_item['quantity']
#             receiving.save()

#         return redirect('cart:show_cart')
#     else:
#         messages.error(request, 'ไม่พบสินค้าในตะกร้า')
#         return redirect('cart:show_cart')


@user_passes_test(is_authorized)
@login_required
def remove_from_cart(request, product_id, receiving_id):
    cart = Cart(request)  # สร้าง instance ของ Cart
    product = get_object_or_404(Product, id=product_id)

    # cart.remove() จะคืนสต็อกไปยัง Receiving โดยอัตโนมัติ
    # (เพราะใน Cart.remove() เราใช้ restore_stock_on_remove=True)
    # *แต่* ในโค้ด Cart.remove() ที่คุณให้มา ไม่ได้รับ restore_stock_on_remove 
    # เป็น argument ในการเรียกใช้เมธอด ให้ดูบรรทัดถัดไป

    # ✅ ต้องเรียก remove แบบนี้เพื่อให้มีการคืนสต็อกกลับไปที่ Receiving
    # (หากคุณต้องการให้การลบจากรถเข็นด้วยตนเอง คืนสต็อกทันที)
    removed_item = cart.remove(product, receiving_id, restore_stock_on_remove=True)
    
    # ⚠️ ข้อควรระวัง: เมธอด remove ในคลาส Cart ที่คุณให้มา
    # ไม่ได้ใส่ restore_stock_on_remove=True เป็นค่า default ในการเรียกใช้
    # หากไม่ใส่ restore_stock_on_remove=True การคืนสต็อกจะเกิดขึ้น
    # เฉพาะตอนที่สินค้าหมดอายุใน __iter__() เท่านั้น
    
    # ดังนั้น การแก้ไขที่ถูกต้องที่สุดคือ:
    removed_item = cart.remove(product, receiving_id, restore_stock_on_remove=True) 

    if removed_item:
        # ✅ โค้ดที่สะอาดและถูกต้อง (Logic การคืนสต็อกถูกย้ายไปที่ Cart.remove() แล้ว)
        messages.success(request, 'ลบสินค้าออกจากตะกร้าแล้ว และคืนสต็อกแล้ว')
        return redirect('cart:show_cart')
    else:
        messages.success(request, 'ลบสินค้าออกจากตะกร้าแล้ว และคืนสต็อกแล้ว')
        messages.error(request, 'ไม่พบสินค้าในตะกร้า')
        return redirect('cart:show_cart')