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

