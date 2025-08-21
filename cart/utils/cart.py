# ใหม่5
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from shop.models import Product, Receiving
from django.contrib import messages
from datetime import datetime, timedelta
from decimal import Decimal

CART_SESSION_ID = 'cart'

# ล่าสุด 14/07/2568
class Cart:
    def __init__(self, request):
        self.session = request.session
        self.request = request  # ✅ เพิ่มเพื่อให้ใช้ messages ได้
        self.cart = self.add_cart_session()

    def __iter__(self):
        product_ids = set()
        expired_items = []

        for product_id, items in self.cart.items():
            for item in items:
                added_time_str = item.get('added_time')
                if added_time_str:
                    added_time = datetime.fromisoformat(added_time_str)
                    if datetime.now() - added_time < timedelta(minutes=2):
                        product_ids.add(int(product_id))
                    else:
                        expired_items.append((int(product_id), item['receiving_id']))

        for product_id, receiving_id in expired_items:
            self.remove(Product.objects.get(id=product_id), receiving_id, restore_stock_on_remove=True)

        products = Product.objects.filter(id__in=product_ids)
        product_map = {str(product.id): product for product in products}

        for product_id in self.cart:
            for item in self.cart[product_id]:
                product = product_map.get(product_id)
                if product:
                    item['product'] = {
                        'id': product.id,
                        'product_id': product.product_id,
                        'product_name': product.product_name,
                        'description': product.description,
                        'unit': product.unit,
                        'image_url': product.image.url if product.image else None,
                    }
                    item['total_price'] = float(Decimal(item['price']) * item['quantity'])
                    yield item

    def add_cart_session(self):
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        return cart

    def add(self, product, quantity, note=''):
        # ✅ ตรวจสอบจำนวนรายการในรถเข็น
        if len(self.cart) >= 5:
            messages.error(self.request, 'ไม่สามารถเพิ่มรายการได้เกิน 5 รายการในรถเข็น!')
            return False

        product_id = str(product.id)
        receivings = Receiving.objects.filter(product=product, quantity__gt=0).order_by('date_created')
        total_receiving_quantity = sum(receiving.quantity for receiving in receivings)

        if quantity > total_receiving_quantity:
            messages.error(self.request, 'จำนวนสินค้าในสต๊อกไม่พอ!')
            return False

        if receivings.exists():
            if product_id not in self.cart:
                self.cart[product_id] = []

            added_quantity = 0
            for receiving in receivings:
                if added_quantity >= quantity:
                    break

                remaining_quantity = quantity - added_quantity
                receiving_used = min(receiving.quantity, remaining_quantity)
                receiving.quantity -= receiving_used
                added_quantity += receiving_used

                # รวมรายการที่ราคาซ้ำกัน
                item_found = False
                for item in self.cart[product_id]:
                    if item['price'] == str(receiving.unitprice):
                        item['quantity'] += receiving_used
                        item_found = True
                        break

                if not item_found:
                    self.cart[product_id].append({
                        'product_id': product_id,
                        'quantity': receiving_used,
                        'price': str(receiving.unitprice),
                        'receiving_id': receiving.id,
                        'date_created': str(receiving.date_created),
                        'note': note,
                        'added_time': datetime.now().isoformat(),
                    })

                product.quantityinstock -= receiving_used
                product.save()
                receiving.save()

            self.save()
            return True
        return False

    def remove(self, product, receiving_id, restore_stock_on_remove=False):
        product_id = str(product.id)
        if product_id in self.cart:
            for item in list(self.cart[product_id]):
                if item['receiving_id'] == receiving_id:
                    quantity = item['quantity']
                    self.cart[product_id].remove(item)
                    if not self.cart[product_id]:
                        del self.cart[product_id]
                    self.save()

                    if restore_stock_on_remove and not self.session.get('cart_cleared'):
                        receiving = Receiving.objects.get(id=receiving_id)
                        receiving.quantity += quantity
                        receiving.save()
                        product.quantityinstock += quantity
                        product.save()
                    return item
        return None

    def save(self):
        self.session.modified = True

    def get_total_price(self):
        return sum(float(item['price']) * item['quantity'] for items in self.cart.values() for item in items)

    def clear(self):
        if CART_SESSION_ID in self.session:
            del self.session[CART_SESSION_ID]
        self.save()

    def logout(self):
        if self.session.get('cart_cleared'):
            return  # ป้องกันการคืนของซ้ำ

        for product_id, items in self.cart.items():
            for item in items:
                receiving = Receiving.objects.get(id=item['receiving_id'])
                product = receiving.product
                product.quantityinstock += item['quantity']
                product.save()
                receiving.quantity += item['quantity']
                receiving.save()

        self.clear()
        self.session['cart_cleared'] = True
        self.save()



        

# เดิมๆ
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
#                 item['total_price'] = float(item['price']) * int(item['quantity'])
#                 yield item

#     def add_cart_session(self):
#         cart = self.session.get(CART_SESSION_ID)
#         if not cart:
#             cart = self.session[CART_SESSION_ID] = {}
#         return cart

#     def add(self, product, quantity, note=''):
#         product_id = str(product.id)
#         receivings = Receiving.objects.filter(product=product, quantity__gt=0).order_by('date_created')

#         total_receiving_quantity = sum(receiving.quantity for receiving in receivings)
#         if quantity > total_receiving_quantity:
#             messages.error(self.request, 'จำนวนสินค้าในสต๊อกไม่พอ!')  # ใช้ self.request
#             return

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

#                     # หาไอเท็มที่มีราคาเดียวกันในรถเข็น
#                     item_found = False
#                     for item in self.cart[product_id]:
#                         if item['price'] == str(receiving.unitprice):
#                             item['quantity'] += receiving_used
#                             item_found = True
#                             break

#                     # ถ้าไม่มีไอเท็มที่มีราคาเดียวกัน ให้สร้างรายการใหม่
#                     if not item_found:
#                         self.cart[product_id].append({
#                             'product_id': product_id,
#                             'quantity': receiving_used,
#                             'price': str(receiving.unitprice),
#                             'receiving_id': receiving.id,
#                             'date_created': str(receiving.date_created),
#                             'note': note,  # เพิ่มหมายเหตุ
#                             'added_time': datetime.now().isoformat(),  # ⬅ เพิ่ม timestamp
#                         })

#                     product.quantityinstock -= receiving_used
#                     product.save()

#                     receiving.save()
#                 else:
#                     break

#             self.save()
#         # else:
#         #     messages.error(self.session, 'สินค้าไม่พร้อมให้บริการในขณะนี้')

#     def remove(self, product, receiving_id):
#         product_id = str(product.id)
#         if product_id in self.cart:
#             for item in self.cart[product_id]:
#                 if item['receiving_id'] == receiving_id:
#                     self.cart[product_id].remove(item)
#                     if not self.cart[product_id]:  # ถ้าไม่มีสินค้าในรายการแล้ว ลบ key ออกจาก dictionary
#                         del self.cart[product_id]
#                     self.save()
#                     return item  # คืนค่ารายการสินค้าที่ถูกลบ
#         return None

#     def save(self):
#         self.session.modified = True

#     def get_total_price(self):
#         return sum(float(item['price']) * item['quantity'] for items in self.cart.values() for item in items)

#     def clear(self):
#         if CART_SESSION_ID in self.session:
#             del self.session[CART_SESSION_ID]
#         self.save()

#     def logout(self):
#         for product_id, items in self.cart.items():
#             for item in items:
#                 receiving_id = item['receiving_id']
#                 receiving = Receiving.objects.get(id=receiving_id)
                    
#                 # คืนจำนวนสินค้ากลับไปยังสต็อกของ Product
#                 product = receiving.product
#                 product.quantityinstock += item['quantity']
#                 product.save()
                    
#                 # อัปเดตจำนวนสินค้าที่รับเข้าใน Receiving
#                 receiving.quantity += item['quantity']
#                 receiving.save()
        
#         # เคลียร์ตะกร้าหลังจาก checkout
#         self.clear()



