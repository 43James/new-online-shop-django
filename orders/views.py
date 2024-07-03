from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from requests.exceptions import ConnectTimeout
from app_linebot.views import notify_admin, notify_user
from shop.models import Receiving
from .models import Order, Issuing
from cart.utils.cart import Cart
from django.http import HttpResponse
import requests


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


def notify_admin(order_id):
    try:
        response = requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers={'Authorization': 'Bearer <YOUR_ACCESS_TOKEN>'},
            json={
                'to': '<ADMIN_USER_ID>',
                'messages': [
                    {
                        'type': 'text',
                        'text': f'New order created with ID: {order_id}'
                    }
                ]
            },
            timeout=10  # เพิ่ม timeout ที่นี่
        )
        response.raise_for_status()
    except ConnectTimeout:
        print("Connection to LINE API timed out.")
    except Exception as e:
        print(f"An error occurred: {e}")

def notify_user(order_id):
    try:
        response = requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers={'Authorization': 'Bearer <YOUR_ACCESS_TOKEN>'},
            json={
                'to': '<USER_ID>',
                'messages': [
                    {
                        'type': 'text',
                        'text': f'Your order with ID: {order_id} has been created'
                    }
                ]
            },
            timeout=10  # เพิ่ม timeout ที่นี่
        )
        response.raise_for_status()
    except ConnectTimeout:
        print("Connection to LINE API timed out.")
    except Exception as e:
        print(f"An error occurred: {e}")

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
            receiving=receiving  # ใช้ Receiving object
        )
    # Notify admin about the new order
    notify_admin(order.id)

    # Notify user about the new order
    notify_user(order.id)  # You can also use notify_user_approved if needed
    
    return redirect('orders:pay_order', order_id=order.id)


@login_required
def checkout(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context = {'title':'Checkout' ,'order':order}
    return render(request, 'checkout.html', context)


@login_required
def fake_payment(request, order_id):
    cart = Cart(request)
    cart.clear()
    order = get_object_or_404(Order, id=order_id)
    # order.status = False
    order.save()
    return redirect('orders:user_orders')


@login_required
def user_orders(request):
    orders = request.user.orders.all()
    context = {'title':'Orders', 'orders': orders}
    return render(request, 'user_orders.html', context)

