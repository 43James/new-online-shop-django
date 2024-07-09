from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from shop.views import custom_404_view  # อิมพอร์ตฟังก์ชัน custom_404_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls', namespace='accounts')),
    path('shop/', include('shop.urls', namespace='shop')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('app_linebot/', include('app_linebot.urls', namespace='app_linebot')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = custom_404_view  # กำหนด custom handler สำหรับ 404 errors
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    