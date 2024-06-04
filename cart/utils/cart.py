# from shop.models import Product
# CART_SESSION_ID = 'cart'


# class Cart:
#     def __init__(self, request):
#         self.session = request.session
#         self.cart = self.add_cart_session()

#     def __iter__(self):
#         product_ids = self.cart.keys()
#         products = Product.objects.filter(id__in=product_ids)
#         cart = self.cart.copy()
#         for product in products:
#             cart[str(product.id)]['product'] = product
#         for item in cart.values():
#             item['total_price'] = int(item['price']) * int(item['quantity'])
#             yield item

#     def add_cart_session(self):
#         cart = self.session.get(CART_SESSION_ID)
#         if not cart:
#             cart = self.session[CART_SESSION_ID] = {}
#         return cart

#     def add(self, product, quantity):
#         product_id = str(product.id)

#         if product_id not in self.cart:
#             self.cart[product_id] = {'quantity': 0, 'price': str(product.unitprice)}

#         self.cart.get(product_id)['quantity'] += quantity
#         self.save()

#     def remove(self, product):
#         product_id = str(product.id)
#         if product_id in self.cart:
#             del self.cart[product_id]
#             self.save()

#     def save(self):
#         self.session.modified = True

#     def get_total_price(self):
#         return sum(int(item['price']) * item['quantity'] for item in self.cart.values())

#     def clear(self):
#         del self.session[CART_SESSION_ID]
#         self.save()


# ใหม่ 1

# from shop.models import Receiving
# from django.shortcuts import get_object_or_404

# CART_SESSION_ID = 'cart'

# class Cart:
#     def __init__(self, request):
#         self.session = request.session
#         self.cart = self.add_cart_session()

#     def __iter__(self):
#         product_ids = self.cart.keys()
#         receivings = Receiving.objects.filter(product__id__in=product_ids).order_by('-date_created')
#         cart = self.cart.copy()
#         for receiving in receivings:
#             product_id = str(receiving.product.id)
#             cart[product_id]['receiving'] = receiving
#             cart[product_id]['total_price'] = receiving.unitprice * cart[product_id]['quantity']
#             yield cart[product_id]

#     def add_cart_session(self):
#         cart = self.session.get(CART_SESSION_ID)
#         if not cart:
#             cart = self.session[CART_SESSION_ID] = {}
#         return cart

#     def add(self, product, quantity):
#         product_id = str(product.id)

#         receiving = Receiving.objects.filter(product=product).order_by('-date_created').first()
#         if receiving:
#             if receiving.quantity <= 0:
#                 # ถ้าสินค้าในสต็อกหมดแล้วให้ยกเลิกการเพิ่มลงในตะกร้า
#                 return

#             # ตรวจสอบว่าจำนวนที่รับเข้ามากกว่าหรือเท่ากับจำนวนที่ต้องการเพิ่มลงในตะกร้าหรือไม่
#             quantity_to_add = min(receiving.quantity, quantity)

#             if product_id not in self.cart:
#                 self.cart[product_id] = {'quantity': 0, 'price': receiving.unitprice}

#             self.cart[product_id]['quantity'] += quantity_to_add
#             self.save()

#             # ลดจำนวนสินค้าที่รับเข้าและบันทึกการเปลี่ยนแปลง
#             receiving.quantity -= quantity_to_add
#             receiving.save()

#     def remove(self, product):
#         product_id = str(product.id)
#         if product_id in self.cart:
#             del self.cart[product_id]
#             self.save()

#     def save(self):
#         self.session.modified = True

#     def get_total_price(self):
#         return sum(item['total_price'] for item in self.cart.values())

#     def clear(self):
#         del self.session[CART_SESSION_ID]
#         self.save()



# ใหม่ 2
# ไฟล์ cart.py

# from shop.models import Product, Receiving
# from django.contrib import messages

# CART_SESSION_ID = 'cart'

# class Cart:
#     def __init__(self, request):
#         self.session = request.session
#         self.cart = self.add_cart_session()

#     def __iter__(self):
#         product_ids = self.cart.keys()
#         products = Product.objects.filter(id__in=product_ids)
#         cart = self.cart.copy()
#         for product in products:
#             cart[str(product.id)]['product'] = product
#         for item in cart.values():
#             item['total_price'] = int(item['price']) * int(item['quantity'])
#             yield item

#     def add_cart_session(self):
#         cart = self.session.get(CART_SESSION_ID)
#         if not cart:
#             cart = self.session[CART_SESSION_ID] = {}
#         return cart

#     def add(self, product, quantity):
#         product_id = str(product.id)
#         receiving = Receiving.objects.filter(product=product_id, quantity__gt=0).order_by('date_created').first()

#         if receiving:
#             if product_id not in self.cart:
#                 self.cart[product_id] = {'quantity': 1, 'price': str(receiving.unitprice)}

#             available_quantity = receiving.quantity
#             if available_quantity >= quantity:
#                 self.cart[product_id]['quantity'] += quantity
#                 receiving.quantity -= quantity
#             else:
#                 self.cart[product_id]['quantity'] += available_quantity
#                 receiving.quantity = 0

#             receiving.save()
#             self.save()
#         else:
#             # ไม่พบการรับเข้าหรือสินค้าหมด
#             messages.error(request, 'สินค้าไม่พร้อมให้บริการในขณะนี้')

#     def remove(self, product):
#         product_id = str(product.id)
#         if product_id in self.cart:
#             del self.cart[product_id]
#             self.save()

#     def save(self):
#         self.session.modified = True

#     def get_total_price(self):
#         return sum(int(item['price']) * item['quantity'] for item in self.cart.values())

#     def clear(self):
#         del self.session[CART_SESSION_ID]
#         self.save()




# ใหม่3
# from shop.models import Product, Receiving
# from django.contrib import messages

# CART_SESSION_ID = 'cart'

# class Cart:
#     def __init__(self, request):
#         self.session = request.session
#         self.cart = self.add_cart_session()

#     def __iter__(self):
#         product_ids = self.cart.keys()
#         products = Product.objects.filter(id__in=product_ids)
#         cart = self.cart.copy()
#         for product in products:
#             cart[str(product.id)]['product'] = product
#         for item in cart.values():
#             item['total_price'] = int(item['price']) * int(item['quantity'])
#             yield item

#     def add_cart_session(self):
#         cart = self.session.get(CART_SESSION_ID)
#         if not cart:
#             cart = self.session[CART_SESSION_ID] = {}
#         return cart

#     def add(self, product, quantity):
#         product_id = str(product.id)
#         receivings = Receiving.objects.filter(product=product, quantity__gt=0).order_by('date_created')

#         if receivings.exists():
#             if product_id not in self.cart:
#                 self.cart[product_id] = {'quantity': 0, 'price': 0, 'receivings': []}

#             added_quantity = 0
#             for receiving in receivings:
#                 if added_quantity < quantity:
#                     remaining_quantity = quantity - added_quantity
#                     if receiving.quantity >= remaining_quantity:
#                         receiving_used = remaining_quantity
#                     else:
#                         receiving_used = receiving.quantity
                    
#                     receiving.quantity -= receiving_used
#                     added_quantity += receiving_used

#                     self.cart[product_id]['quantity'] += receiving_used
#                     self.cart[product_id]['price'] = str(receiving.unitprice)  # Assuming the price is the same
#                     self.cart[product_id]['receivings'].append({
#                         'receiving_id': receiving.id,
#                         'quantity': receiving_used,
#                         'date_created': str(receiving.date_created)
#                     })
                    
#                     receiving.save()
#                 else:
#                     break

#             self.save()
#         else:
#             messages.error(request, 'สินค้าไม่พร้อมให้บริการในขณะนี้')

#     def remove(self, product):
#         product_id = str(product.id)
#         if product_id in self.cart:
#             receivings_info = self.cart[product_id]['receivings']
#             for receiving_info in receivings_info:
#                 receiving = Receiving.objects.get(id=receiving_info['receiving_id'])
#                 receiving.quantity += receiving_info['quantity']
#                 receiving.save()
            
#             del self.cart[product_id]
#             self.save()

#     def save(self):
#         self.session.modified = True

#     def get_total_price(self):
#         return sum(int(item['price']) * item['quantity'] for item in self.cart.values())

#     def clear(self):
#         del self.session[CART_SESSION_ID]
#         self.save()




# ใหม่4
# from shop.models import Product, Receiving
# from django.contrib import messages

# CART_SESSION_ID = 'cart'

# class Cart:
#     def __init__(self, request):
#         self.session = request.session
#         self.cart = self.add_cart_session()

#     def __iter__(self):
#         product_ids = set()
#         for items in self.cart.values():
#             for item in items:
#                 product_ids.add(item['product_id'])

#         products = Product.objects.filter(id__in=product_ids)
#         product_map = {product.id: product for product in products}

#         for items in self.cart.values():
#             for item in items:
#                 item['product'] = product_map[int(item['product_id'])]
#                 item['total_price'] = int(item['price']) * int(item['quantity'])
#                 yield item

#     def add_cart_session(self):
#         cart = self.session.get(CART_SESSION_ID)
#         if not cart:
#             cart = self.session[CART_SESSION_ID] = {}
#         return cart

#     def add(self, product, quantity):
#         product_id = str(product.id)
#         receivings = Receiving.objects.filter(product=product, quantity__gt=0).order_by('date_created')

#         if receivings.exists():
#             if product_id not in self.cart:
#                 self.cart[product_id] = []

#             added_quantity = 0
#             for receiving in receivings:
#                 if added_quantity < quantity:
#                     remaining_quantity = quantity - added_quantity
#                     if receiving.quantity >= remaining_quantity:
#                         receiving_used = remaining_quantity
#                     else:
#                         receiving_used = receiving.quantity

#                     receiving.quantity -= receiving_used
#                     added_quantity += receiving_used

#                     self.cart[product_id].append({
#                         'product_id': product_id,
#                         'quantity': receiving_used,
#                         'price': str(receiving.unitprice),
#                         'receiving_id': receiving.id,
#                         'date_created': str(receiving.date_created)
#                     })

#                     receiving.save()
#                 else:
#                     break

#             self.save()
#         else:
#             messages.error(request, 'สินค้าไม่พร้อมให้บริการในขณะนี้')

#     def remove(self, product):
#         product_id = str(product.id)
#         if product_id in self.cart:
#             items_to_remove = self.cart[product_id]
#             for item in items_to_remove:
#                 receiving = Receiving.objects.get(id=item['receiving_id'])
#                 receiving.quantity += item['quantity']
#                 receiving.save()

#             del self.cart[product_id]
#             self.save()

#     def save(self):
#         self.session.modified = True

#     def get_total_price(self):
#         return sum(int(item['price']) * item['quantity'] for items in self.cart.values() for item in items)

#     def clear(self):
#         del self.session[CART_SESSION_ID]
#         self.save()




# ใหม่5
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from shop.models import Product, Receiving
from django.contrib import messages

CART_SESSION_ID = 'cart'

class Cart:
    def __init__(self, request):
        self.session = request.session
        self.cart = self.add_cart_session()

    def __iter__(self):
        product_ids = set()
        for items in self.cart.values():
            for item in items:
                product_ids.add(item['product_id'])

        products = Product.objects.filter(id__in=product_ids)
        product_map = {product.id: product for product in products}

        for items in self.cart.values():
            for item in items:
                item['product'] = product_map[int(item['product_id'])]
                item['total_price'] = int(item['price']) * int(item['quantity'])
                yield item

    def add_cart_session(self):
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        return cart

    def add(self, product, quantity):
        product_id = str(product.id)
        receivings = Receiving.objects.filter(product=product, quantity__gt=0).order_by('date_created')

        total_receiving_quantity = sum(receiving.quantity for receiving in receivings)
        if quantity > total_receiving_quantity:
            messages.error(self.request, 'จำนวนสินค้าในสต๊อกไม่พอ!')  # ใช้ self.request
            return

        if receivings.exists():
            if product_id not in self.cart:
                self.cart[product_id] = []

            added_quantity = 0
            for receiving in receivings:
                if added_quantity < quantity:
                    remaining_quantity = quantity - added_quantity
                    if receiving.quantity >= remaining_quantity:
                        receiving_used = remaining_quantity
                    else:
                        receiving_used = receiving.quantity

                    receiving.quantity -= receiving_used
                    added_quantity += receiving_used

                    # หาไอเท็มที่มีราคาเดียวกันในรถเข็น
                    item_found = False
                    for item in self.cart[product_id]:
                        if item['price'] == str(receiving.unitprice):
                            item['quantity'] += receiving_used
                            item_found = True
                            break

                    # ถ้าไม่มีไอเท็มที่มีราคาเดียวกัน ให้สร้างรายการใหม่
                    if not item_found:
                        self.cart[product_id].append({
                            'product_id': product_id,
                            'quantity': receiving_used,
                            'price': str(receiving.unitprice),
                            'receiving_id': receiving.id,
                            'date_created': str(receiving.date_created)
                        })

                    receiving.save()
                else:
                    break

            self.save()
        # else:
        #     messages.error(self.session, 'สินค้าไม่พร้อมให้บริการในขณะนี้')

    def remove(self, product, receiving_id):
        product_id = str(product.id)
        if product_id in self.cart:
            for item in self.cart[product_id]:
                if item['receiving_id'] == receiving_id:
                    self.cart[product_id].remove(item)
                    if not self.cart[product_id]:  # ถ้าไม่มีสินค้าในรายการแล้ว ลบ key ออกจาก dictionary
                        del self.cart[product_id]
                    self.save()
                    return item  # คืนค่ารายการสินค้าที่ถูกลบ
        return None

    def save(self):
        self.session.modified = True

    def get_total_price(self):
        return sum(int(item['price']) * item['quantity'] for items in self.cart.values() for item in items)

    def clear(self):
        if CART_SESSION_ID in self.session:
            del self.session[CART_SESSION_ID]
        self.save()

    def logout(self):
        for product_id, items in self.cart.items():
            for item in items:
                receiving_id = item['receiving_id']
                receiving = Receiving.objects.get(id=receiving_id)
                    
                # คืนจำนวนสินค้ากลับไปยังสต็อกของ Product
                # product = receiving.product
                # product.quantityinstock += item['quantity']
                # product.save()
                    
                # อัปเดตจำนวนสินค้าที่รับเข้าใน Receiving
                receiving.quantity += item['quantity']
                receiving.save()
        
        # เคลียร์ตะกร้าหลังจาก checkout
        self.clear()




    # @receiver(user_logged_in)
    # def merge_session_cart(sender, request, user, **kwargs):
    #     # หากมีรถเข็นในเซสชันของผู้ใช้เมื่อเข้าสู่ระบบ
    #     if CART_SESSION_ID in request.session:
    #         user_cart = Cart(request)  # สร้างรถเข็นของผู้ใช้
    #         session_cart = request.session[CART_SESSION_ID]  # รถเข็นในเซสชันปัจจุบัน

    #         # เพิ่มรายการสินค้าจากรถเข็นในเซสชันไปยังรถเข็นของผู้ใช้
    #         for product_id, items in session_cart.items():
    #             for item in items:
    #                 product = Product.objects.get(id=item['product_id'])
    #                 user_cart.add(product, item['quantity'])

    #         # ล้างรถเข็นในเซสชัน
    #         del request.session[CART_SESSION_ID]
    #         user_cart.save()

    # @receiver(user_logged_out)
    # def save_session_cart(sender, request, user, **kwargs):
    #     # หากมีรถเข็นของผู้ใช้ในระบบ
    #     if request.user is not None and request.user.is_authenticated:
    #         user_cart = Cart(request)
    #         session_cart = user_cart.cart

    #         # เก็บรถเข็นของผู้ใช้ในเซสชัน
    #         request.session[CART_SESSION_ID] = session_cart


















# กรณณีใช้กับตาราง receiving

# from django.urls import reverse
# from shop.models import Receiving

# CART_SESSION_ID = 'cart'

# class Cart:
#     def __init__(self, request):
#         self.session = request.session
#         self.cart = self.add_cart_session()

#     def __iter__(self):
#         receiving_ids = self.cart.keys()
#         receivings = Receiving.objects.filter(id__in=receiving_ids)
#         cart = self.cart.copy()
#         for receiving in receivings:
#             cart[str(receiving.id)]['receiving'] = receiving
#         for item in cart.values():
#             item['total_price'] = int(item['price']) * int(item['quantity'])
#             yield item

#     def add_cart_session(self):
#         cart = self.session.get(CART_SESSION_ID)
#         if not cart:
#             cart = self.session[CART_SESSION_ID] = {}
#         return cart

#     def add(self, receiving, quantity):
#         receiving_id = str(receiving.id)

#         if receiving_id not in self.cart:
#             self.cart[receiving_id] = {'quantity': 0, 'price': str(receiving.unitprice)}

#         self.cart.get(receiving_id)['quantity'] += quantity
#         self.save()

#     def remove(self, receiving):
#         receiving_id = str(receiving.id)
#         if receiving_id in self.cart:
#             del self.cart[receiving_id]
#             self.save()

#     def save(self):
#         self.session.modified = True

#     def get_total_price(self):
#         return sum(int(item['price']) * item['quantity'] for item in self.cart.values())

#     def clear(self):
#         del self.session[CART_SESSION_ID]
#         self.save()
