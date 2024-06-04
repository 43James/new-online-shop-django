from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from cart.utils.cart import Cart
from .forms import QuantityForm
from shop.models import Product, Receiving



# เดิม
# @login_required
# def add_to_cart(request, product_id):
#     cart = Cart(request)
#     product = get_object_or_404(Product, id=product_id)
#     form = QuantityForm(request.POST)
#     if form.is_valid():
#         data = form.cleaned_data
#         cart.add(product=product, quantity=data['quantity'])
#         product.quantityinstock -= data['quantity']  # ลดจำนวนสินค้าในสต๊อก
#         product.save()
#         messages.success(request, 'เพิ่มลงในตะกร้าแล้ว!')
#     return redirect('shop:product_detail', slug=product.slug)

# ใหม่1
# @login_required
# def add_to_cart(request, product_id):
#     cart = Cart(request)
#     product = get_object_or_404(Product, id=product_id)
#     form = QuantityForm(request.POST)
#     if form.is_valid():
#         data = form.cleaned_data
#         quantity_to_add = data['quantity']
        
#         if quantity_to_add > product.quantityinstock:
#             messages.error(request, 'จำนวนสินค้าในสต๊อกไม่พอ!')
#         else:
#             cart.add(product=product, quantity=quantity_to_add)
#             product.quantityinstock -= quantity_to_add  # ลดจำนวนสินค้าในสต๊อก
#             product.save()
#             messages.success(request, 'เพิ่มลงในตะกร้าแล้ว!')
#     return redirect('shop:product_detail', slug=product.slug)

# แก้ไขใหม่1
# @login_required
# def add_to_cart(request, product_id):
#     cart = Cart(request)
#     product = get_object_or_404(Product, id=product_id)
#     form = QuantityForm(request.POST)
    
#     if form.is_valid():
#         data = form.cleaned_data
#         quantity_to_add = data['quantity']
        
#         cart.add(product=product, quantity=quantity_to_add)
#         messages.success(request, 'เพิ่มลงในตะกร้าแล้ว!')
    
#     return redirect('shop:product_detail', slug=product.slug)

# ใหม่2
@login_required
def add_to_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = QuantityForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        quantity_to_add = data['quantity']
        
        receivings = Receiving.objects.filter(product=product, quantity__gt=0).order_by('date_created')
        total_receiving_quantity = sum(receiving.quantity for receiving in receivings)
        if quantity_to_add > total_receiving_quantity:
            messages.error(request, 'จำนวนสินค้าในสต็อกไม่เพียงพอ!')
        else:
            cart.add(product=product, quantity=quantity_to_add)
            messages.success(request, 'เพิ่มลงในรถเข็น!')
    else:
        messages.error(request, 'กรุณาเพิ่มสินค้าลงในรถเข็น!')
    return redirect('shop:product_detail', slug=product.slug)


@login_required
def show_cart(request):
    cart = Cart(request)
    context = {'title': 'Cart', 'cart': cart}
    return render(request, 'cart.html', context)


# @login_required
# def remove_from_cart(request, product_id):
#     cart = Cart(request)
#     product = get_object_or_404(Product, id=product_id)

#     # ตรวจสอบว่า product_id มีอยู่ใน cart หรือไม่
#     if str(product_id) in cart.cart:
#         # เก็บข้อมูลสินค้าก่อนลบ
#         removed_item = cart.cart[str(product_id)].copy()
#         cart.remove(product)

#         # เพิ่มจำนวนสินค้าในสต็อกเมื่อลบออกจากตะกร้า
#         product.quantityinstock += removed_item['quantity']
#         product.save()

#         return redirect('cart:show_cart')
#     else:
#         messages.error(request, 'ไม่พบสินค้าในตะกร้า')
#         return redirect('cart:show_cart')



# ใหม่ 1 
# from django.db import transaction  # import transaction

# @login_required
# def remove_from_cart(request, product_id):
#     cart = Cart(request)
#     product = get_object_or_404(Product, id=product_id)

#     # ตรวจสอบว่า product_id มีอยู่ใน cart หรือไม่
#     if str(product_id) in cart.cart:
#         # เก็บข้อมูลสินค้าก่อนลบ
#         removed_item = cart.cart[str(product_id)].copy()
#         cart.remove(product)

#         # ใช้ transaction.atomic() เพื่อให้การเปลี่ยนแปลงข้อมูลเกิดขึ้นในการทำงานเดียวกัน
#         with transaction.atomic():
#             # เพิ่มจำนวนสินค้าในสต็อกเมื่อลบออกจากตะกร้า (ในตาราง Product)
#             product.quantityinstock += removed_item['quantity']
#             product.save()

#             # เพิ่มจำนวนสินค้าในสต็อกเมื่อลบออกจากตะกร้า (ในตาราง Receiving)
#             receiving = Receiving.objects.filter(product=product_id).first()
#             if receiving:  # ตรวจสอบว่ามีการรับเข้าสินค้าหรือไม่
#                 receiving.quantity += removed_item['quantity']  # เพิ่มจำนวนสินค้าที่รับเข้า
#                 receiving.save()  # บันทึกการเปลี่ยนแปลง

#         return redirect('cart:show_cart')
#     else:
#         messages.error(request, 'ไม่พบสินค้าในตะกร้า')
#         return redirect('cart:show_cart')



# ใหม่ 2
# from django.db import transaction  # import transaction

# @login_required
# def remove_from_cart(request, product_id):
#     cart = Cart(request)
#     product = get_object_or_404(Product, id=product_id)

#     # ตรวจสอบว่า product_id มีอยู่ใน cart หรือไม่
#     if str(product_id) in cart.cart:
#         # เก็บข้อมูลสินค้าก่อนลบ
#         removed_item = cart.cart[str(product_id)].copy()
#         cart.remove(product)

#         # ใช้ transaction.atomic() เพื่อให้การเปลี่ยนแปลงข้อมูลเกิดขึ้นในการทำงานเดียวกัน
#         with transaction.atomic():
#             # เพิ่มจำนวนสินค้าในสต็อกเมื่อลบออกจากตะกร้า (ในตาราง Product)
#             product.quantityinstock += removed_item['quantity']
#             product.save()

#             # เพิ่มจำนวนสินค้าในสต็อกเมื่อลบออกจากตะกร้า (ในตาราง Receiving)
#             receiving = Receiving.objects.filter(product=product_id, quantity__gt=0).order_by('date_created').first()
#             if receiving:  # ตรวจสอบว่ามีการรับเข้าสินค้าหรือไม่
#                 receiving.quantity += removed_item['quantity']  # เพิ่มจำนวนสินค้าที่รับเข้า
#                 receiving.save()  # บันทึกการเปลี่ยนแปลง

#         return redirect('cart:show_cart')
#     else:
#         messages.error(request, 'ไม่พบสินค้าในตะกร้า')
#         return redirect('cart:show_cart')



# ใหม่3
from django.db import transaction  # import transaction

# @login_required
# def remove_from_cart(request, product_id):
#     cart = Cart(request)
#     product = get_object_or_404(Product, id=product_id)

#     # ตรวจสอบว่า product_id มีอยู่ใน cart หรือไม่
#     if str(product_id) in cart.cart:
#         # เก็บข้อมูลสินค้าก่อนลบ
#         removed_item = cart.cart[str(product_id)].copy()
#         cart.remove(product)

#         # ใช้ transaction.atomic() เพื่อให้การเปลี่ยนแปลงข้อมูลเกิดขึ้นในการทำงานเดียวกัน
#         with transaction.atomic():
#             # เพิ่มจำนวนสินค้าในสต็อกเมื่อลบออกจากตะกร้า (ในตาราง Product)
#             product.quantityinstock += removed_item['quantity']
#             product.save()

#             # เพิ่มจำนวนสินค้าในสต็อกเมื่อลบออกจากตะกร้า (ในตาราง Receiving)
#             receiving = Receiving.objects.filter(product=product_id, quantity__gt=0).order_by('date_created').first()
#             if receiving:  # ตรวจสอบว่ามีการรับเข้าสินค้าหรือไม่
#                 receiving.quantity += removed_item['quantity']  # เพิ่มจำนวนสินค้าที่รับเข้า
#                 receiving.save()  # บันทึกการเปลี่ยนแปลง
            

#         return redirect('cart:show_cart')
#     else:
#         messages.error(request, 'ไม่พบสินค้าในตะกร้า')
#         return redirect('cart:show_cart')


# ใหม่4
# @login_required
# def remove_from_cart(request, product_id):
#     cart = Cart(request)
#     product = get_object_or_404(Product, id=product_id)

#     # ตรวจสอบว่า product_id มีอยู่ใน cart หรือไม่
#     if str(product_id) in cart.cart:
#         # เก็บข้อมูลสินค้าก่อนลบ
#         removed_item = cart.cart[str(product_id)].copy()
#         cart.remove(product)

#         # ใช้ transaction.atomic() เพื่อให้การเปลี่ยนแปลงข้อมูลเกิดขึ้นในการทำงานเดียวกัน
#         with transaction.atomic():
#             # เพิ่มจำนวนสินค้าในสต็อกเมื่อลบออกจากตะกร้า (ในตาราง Product)
#             product.quantityinstock += removed_item['quantity']
#             product.save()

#             # คืนจำนวนสินค้าในสต็อกเมื่อลบออกจากตะกร้า (ในตาราง Receiving)
#             # for receiving_info in removed_item['receivings']:
#             #     receiving = Receiving.objects.get(id=receiving_info['receiving_id'])
#             #     receiving.quantity += receiving_info['quantity']
#             #     receiving.save()

#         return redirect('cart:show_cart')
#     else:
#         messages.error(request, 'ไม่พบสินค้าในตะกร้า')
#         return redirect('cart:show_cart')



# ใหม่5
# @login_required
# def remove_from_cart(request, product_id):
#     cart = Cart(request)
#     product = get_object_or_404(Product, id=product_id)

#     if str(product_id) in cart.cart:
#         items_to_remove = cart.cart[str(product_id)].copy()
#         cart.remove(product)

#         with transaction.atomic():
#             product.quantityinstock += sum(item['quantity'] for item in items_to_remove)
#             product.save()

#             for item in items_to_remove:
#                 receiving = Receiving.objects.get(id=item['receiving_id'])
#                 receiving.quantity += item['quantity']
#                 receiving.save()

#         return redirect('cart:show_cart')
#     else:
#         messages.error(request, 'ไม่พบสินค้าในตะกร้า')
#         return redirect('cart:show_cart')

# ใหม่6
# @login_required
# def remove_from_cart(request, product_id):
#     cart = Cart(request)  # สร้าง instance ของ Cart
#     product = get_object_or_404(Product, id=product_id)

#     if str(product_id) in cart.cart:
#         items_to_remove = cart.cart[str(product_id)].copy()
#         cart.remove(product)

#         with transaction.atomic():
#             product.quantityinstock += sum(item['quantity'] for item in items_to_remove)
#             product.save()

#             for item in items_to_remove:
#                 receiving = Receiving.objects.get(id=item['receiving_id'])
#                 receiving.quantity += item['quantity']
#                 receiving.save()

#         return redirect('cart:show_cart')
#     else:
#         messages.error(request, 'ไม่พบสินค้าในตะกร้า')
#         return redirect('cart:show_cart')



# ใหม่7
@login_required
def remove_from_cart(request, product_id, receiving_id):
    cart = Cart(request)  # สร้าง instance ของ Cart
    product = get_object_or_404(Product, id=product_id)

    removed_item = cart.remove(product, receiving_id)  # ลบสินค้าด้วย receiving_id

    if removed_item:
        with transaction.atomic():
            # product.quantityinstock += removed_item['quantity']
            # product.save() # กรณีปิดไว้ไม่คืนจำนวนกลับไปยังสต๊อกในโปรดั๊กแล้ว

            receiving = Receiving.objects.get(id=removed_item['receiving_id'])
            receiving.quantity += removed_item['quantity']
            receiving.save()

        return redirect('cart:show_cart')
    else:
        messages.error(request, 'ไม่พบสินค้าในตะกร้า')
        return redirect('cart:show_cart')














# กรณีใช้กับ ตารางรับเข้า

# @login_required
# def add_to_cart(request, product_id):
#     cart = Cart(request)
#     product = get_object_or_404(Product, id=product_id)
#     receiving = Receiving.objects.filter(product=product).order_by('date_created').first()  # รับเข้าครั้งแรก
#     form = QuantityForm(request.POST)
    
#     if form.is_valid():
#         data = form.cleaned_data
#         if receiving:  # ตรวจสอบว่ามีการรับเข้าหรือไม่
#             if receiving.quantityreceived > 0:  # ตรวจสอบว่ามีจำนวนที่รับเข้ามากกว่าศูนย์หรือไม่
#                 if data['quantity'] <= receiving.quantityreceived:  # ตรวจสอบว่าจำนวนที่ใส่เข้ามาไม่เกินจำนวนที่รับเข้า
#                     if receiving.quantity >= data['quantity']:
#                         receiving.quantity -= data['quantity']
#                         receiving.save()
#                         cart.add(product=product, quantity=data['quantity'])
#                         messages.success(request, 'เพิ่มลงในตะกร้าแล้ว!')
#                     else:
#                         messages.error(request, 'จำนวนที่ใส่มากกว่าจำนวนที่รับเข้า')
#                 else:
#                     messages.error(request, 'จำนวนที่ใส่มากกว่าจำนวนที่รับเข้า')
#             else:
#                 messages.error(request, 'ยังไม่มีสินค้าที่รับเข้า')
#         else:
#             messages.error(request, 'ยังไม่มีสินค้าที่รับเข้า')
    
#     return redirect('shop:product_detail', id=product.id)



# @login_required
# def add_to_cart(request, product_id):
#     cart = Cart(request)
#     product = get_object_or_404(Product, id=product_id)
#     receiving_instances = Receiving.objects.filter(product=product)

#     # เลือกจากรายการแรกหรือทุกรายการ ขึ้นอยู่กับความเหมาะสมของแอปพลิเคชันของคุณ
#     receiving = receiving_instances.first()

#     form = QuantityForm(request.POST)
    
#     if form.is_valid():
#         data = form.cleaned_data
#         cart.add(product=product, quantity=data['quantity'])

#         # ลดจำนวนสินค้าใน Receiving หรือในทุกรายการที่เลือกได้
#         for receiving in receiving_instances:
#             receiving.quantity -= data['quantity']
#             receiving.save()
#         messages.success(request, 'เพิ่มลงในตะกร้าแล้ว!')
    
#     return redirect('shop:product_detail', id=product.id)


