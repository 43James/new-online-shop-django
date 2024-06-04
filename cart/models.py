from django.db import models
from django.conf import settings
from accounts.models import MyUser
from shop.models import Product  # แนะนำให้เปลี่ยน Product เป็นชื่อโมเดลที่ถูกต้อง

# class CartItem(models.Model):
#     user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField()
#     price = models.PositiveIntegerField()

#     def get_total(self):
#         return self.product.price * self.quantity
    