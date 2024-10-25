from collections import defaultdict
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from requests.exceptions import ConnectTimeout
from app_linebot.views import notify_admin, notify_admin_receive_confirmation, notify_user
from dashboard.views import convert_to_buddhist_era, thai_month_name
from orders.forms import UserApproveForm
from shop.models import Receiving
from shop.views import count_unconfirmed_orders
from .models import Order, Issuing
from cart.utils.cart import Cart
from django.http import Http404, HttpResponse
import requests
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from datetime import datetime, timedelta


# def thai_month_name(month):
#     thai_months = [
#         'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน',
#         'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม',
#         'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
#     ]
#     return thai_months[month - 1] if 1 <= month <= 12 else ''

# def convert_to_buddhist_era(year):
#     return year + 543

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


# def notify_admin(order_id):
#     try:
#         response = requests.post(
#             'https://api.line.me/v2/bot/message/push',
#             headers={'Authorization': 'Bearer <YOUR_ACCESS_TOKEN>'},
#             json={
#                 'to': '<ADMIN_USER_ID>',
#                 'messages': [
#                     {
#                         'type': 'text',
#                         'text': f'New order created with ID: {order_id}'
#                     }
#                 ]
#             },
#             timeout=10  # เพิ่ม timeout ที่นี่
#         )
#         response.raise_for_status()
#     except ConnectTimeout:
#         print("Connection to LINE API timed out.")
#     except Exception as e:
#         print(f"An error occurred: {e}")



# def notify_user(order_id):
#     try:
#         response = requests.post(
#             'https://api.line.me/v2/bot/message/push',
#             headers={'Authorization': 'Bearer <YOUR_ACCESS_TOKEN>'},
#             json={
#                 'to': '<USER_ID>',
#                 'messages': [
#                     {
#                         'type': 'text',
#                         'text': f'Your order with ID: {order_id} has been created'
#                     }
#                 ]
#             },
#             timeout=10  # เพิ่ม timeout ที่นี่
#         )
#         response.raise_for_status()
#     except ConnectTimeout:
#         print("Connection to LINE API timed out.")
#     except Exception as e:
#         print(f"An error occurred: {e}")


@user_passes_test(is_authorized)
@login_required
def create_order(request):
    cart = Cart(request)
    order = Order.objects.create(user=request.user)
    for item in cart:
        receiving = get_object_or_404(Receiving, id=item['receiving_id'])  # ดึง Receiving object
        Issuing.objects.create(
            order=order,
            product=item['product'],
            price=item['price'],
            quantity=item['quantity'],
            receiving=receiving,  # ใช้ Receiving object
            note=item['note']  # เพิ่มหมายเหตุในรายการ Issuing
        )
    # Notify admin about the new order
    # notify_admin(request, order.id)

    # Notify user about the new order
    # notify_user(order.id)  # You can also use notify_user_approved if needed
    
    return redirect('orders:pay_order', order_id=order.id)


@user_passes_test(is_authorized)
@login_required
def checkout(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context = {'title':'Checkout' ,'order':order}
    return render(request, 'checkout.html', context)


@user_passes_test(is_authorized)
@login_required
def fake_payment(request, order_id):
    cart = Cart(request)
    cart.clear()
    order = get_object_or_404(Order, id=order_id)
    # order.status = False
    order.save()
    return redirect('orders:user_orders')


@user_passes_test(is_authorized)
@login_required
def user_orders(request):
    # orders = request.user.orders.all()
    now = datetime.now()

    # ใช้เดือนและปีปัจจุบันหากไม่ได้ระบุในพารามิเตอร์ GET
    last_month = now.month if now.month > 1 else 12
    last_year = now.year if now.month > 1 else now.year - 1

    # ตรวจสอบว่ามีการระบุเดือนและปีในพารามิเตอร์ GET หรือไม่ ถ้าไม่มีใช้เดือนและปีของเดือนที่แล้ว
    month = int(request.GET.get('month', last_month))
    year_buddhist = int(request.GET.get('year', last_year + 543))

    # แปลงปี พ.ศ. เป็น ค.ศ. สำหรับการค้นหาในฐานข้อมูล
    year_ad = year_buddhist - 543

    # ดึงข้อมูลรับเข้าสินค้าที่มีเดือนและปีที่ระบุสำหรับผู้ใช้งานปัจจุบัน
    orders = request.user.orders.filter(
        month=month,
        year=year_ad
     ).select_related('user')
    
    unconfirmed_count = count_unconfirmed_orders(request.user)
    
    context = { 'title':'Orders', 
                'orders': orders,
                'selected_month': month,
                'selected_year': year_buddhist,
                'years': range(2020 + 543, datetime.now().year + 1 + 543),
                'months': [
                (1, 'มกราคม'), (2, 'กุมภาพันธ์'), (3, 'มีนาคม'), (4, 'เมษายน'),
                (5, 'พฤษภาคม'), (6, 'มิถุนายน'), (7, 'กรกฎาคม'), (8, 'สิงหาคม'),
                (9, 'กันยายน'), (10, 'ตุลาคม'), (11, 'พฤศจิกายน'), (12, 'ธันวาคม')],
                'month_name': thai_month_name(month),
                'count_unconfirmed_orders': unconfirmed_count, 
               }
    
    previous_month = month - 1 if month > 1 else 12
    previous_year = year_ad if month > 1 else year_ad - 1
    context['previous_month_name'] = thai_month_name(previous_month)
    context['previous_year_buddhist'] = convert_to_buddhist_era(previous_year)
    return render(request, 'user_orders.html', context)


@user_passes_test(is_authorized)
@login_required
def monthly_totals_view(request):
    # orders = request.user.orders.all()  # กรองเฉพาะ order ของผู้ใช้งานปัจจุบันที่เข้าสู่ระบบ
    # กรองเฉพาะ order ของผู้ใช้งานปัจจุบันที่เข้าสู่ระบบ และมีสถานะออเดอร์เป็น True
    orders = request.user.orders.filter(status=True)
    monthly_totals = defaultdict(Decimal)
    count_unconfirmed = count_unconfirmed_orders(request.user)
    
    for order in orders:
        for item in order.items.all():
            # ใช้ tuple (order.month, order.year) เป็น key
            monthly_totals[(order.month, order.year)] += item.get_cost()
    
    # แปลงค่าใน monthly_totals เป็น float เพื่อให้สามารถใช้งานใน template ได้
    monthly_totals_float = {(month, year): float(total) for (month, year), total in monthly_totals.items()}
    
    context = {
        'title': 'Monthly Totals',
        'monthly_totals': monthly_totals_float,
        'count_unconfirmed_orders': count_unconfirmed,
    }
    return render(request, 'monthly_totals.html', context)


# เพิ่มการเรียกใช้ฟังก์ชัน notify_admin_receive_confirmation ใน view function user_approve
@login_required
def user_approve(request, order_id):
    ap = get_object_or_404(Order, id=order_id)
    form = UserApproveForm(request.POST, instance=ap)
    
    if request.method == 'POST':
        if form.is_valid():
            print("ยืนยันการรับวัสดุสำเร็จ")
            form.save()
            notify_admin_receive_confirmation(order_id)  # เรียกฟังก์ชันการแจ้งเตือนแอดมิน
            # messages.success(request, 'ยืนยันการรับวัสดุสำเร็จ')
            return redirect(reverse('orders:user_orders') + '?success=true')
        else:
            messages.error(request, 'ดำเนินการไม่สำเร็จ')
    else:
        form = UserApproveForm(instance=ap)
        
    return render(request, 'orders.html', {
        'ap': ap,
        'form': form,
    })







# เดิม
# @login_required
# def create_order(request):
#     cart = Cart(request)
#     order = Order.objects.create(user=request.user)
#     for item in cart:
#         Issuing.objects.create(
#             order=order, 
#             product=item['product'],
#             price=item['price'], 
#             quantity=item['quantity']
#     )
#      # Notify admin about the new order
#     notify_admin(order.id)

#     # Notify user about the new order
#     notify_user(order.id)  # You can also use notify_user_approved if needed
    
#     return redirect('orders:pay_order', order_id=order.id)