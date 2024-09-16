# Create your views here.
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import pytz
from accounts.models import MyUser
from orders.models import Order
from .models import UserLine
from linebot import LineBotApi
from linebot.models import TextSendMessage
import json


line_bot_api = LineBotApi('p/7wo/1oBrhYYteqvWuGQQJz5AADd3pnSiyTJByIju6L6rT5fWsifmzRiD8YOoPHYZkSQHNMIcnAyjMq9ad3zjL4LHn4+C5PubjxDeGXrcXO5XIYd65jHw2slPVxQ7akCkzj0ZC+8MRIJ3oIBRpHLAdB04t89/1O/w1cDnyilFU=')

@csrf_exempt
def linebot(request):
    print(request.method)

    if request.method == 'POST':
        try:
            body = request.body.decode('utf-8')
            body = json.loads(body)
            events = body.get('events', [])

            if events:
                event = events[0]
                text = event.get('message', {}).get('text', '')

                if text.startswith('ผูกบัญชี'):
                    a = text.split()
                    if len(a) == 2:
                        username = a[1]
                        user = MyUser.objects.filter(username=username).first()

                        if user:
                            line = UserLine.objects.filter(user=user).first()
                            userId = event.get('source', {}).get('userId', '')
                            print(user)
                            print(userId)

                            if not line:
                                line = UserLine(user=user, userId=userId)
                                line.save()

                                # ส่งข้อความแจ้งเตือนผู้ใช้
                                line_bot_api.push_message(userId, TextSendMessage(text='ผูกบัญชีสำเร็จ✅'))

                            else:
                                line.userId = userId
                                line.save()

                                # ส่งข้อความแจ้งเตือนผู้ใช้ (กรณีอัพเดตการผูกบัญชี)
                                line_bot_api.push_message(userId, TextSendMessage(text='อัพเดตการผูกบัญชีสำเร็จ✅'))
                        else:
                            # ส่งข้อความแจ้งเตือนถ้า username ไม่ถูกต้อง
                            userId = event.get('source', {}).get('userId', '')
                            line_bot_api.push_message(userId, TextSendMessage(text='⚠ Username ไม่ถูกต้อง❗\nกรุณาตรวจสอบและลองใหม่อีกครั้ง'))
                    else:
                        # ส่งข้อความแจ้งเตือนถ้ามีการป้อนข้อมูลไม่ครบ
                        userId = event.get('source', {}).get('userId', '')
                        line_bot_api.push_message(userId, TextSendMessage(text='⚠ กรุณาพิมพ์คำว่า "ผูกบัญชี ตามด้วย Username ของคุณค่ะ"'))
                else:
                    # ส่งข้อความแจ้งเตือนว่าข้อความไม่ถูกต้อง
                    userId = event.get('source', {}).get('userId', '')
                    line_bot_api.push_message(userId, TextSendMessage(text='⚠ ข้อความไม่ถูกต้อง❗\nกรุณาพิมพ์คำว่า "ผูกบัญชี ตามด้วย Username ของคุณค่ะ"'))

        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")

    return render(request, "home_page.html")



def notify_admin_cancel(order_id, reason):
    order = Order.objects.filter(id=order_id).first()
    if order:
        # ค้นหาผู้ใช้งานที่เป็น manager และ admin
        users_to_notify = MyUser.objects.filter(is_manager=True) | MyUser.objects.filter(is_admin=True)

        # ดึง Line User IDs ของผู้ใช้งานเหล่านี้
        admin_user_ids = []
        for user in users_to_notify:
            try:
                user_line = UserLine.objects.get(user=user)
                admin_user_ids.append(user_line.userId)
            except UserLine.DoesNotExist:
                print(f"ไม่มี Line ID สำหรับผู้ใช้ {user.username}")

        # สร้างข้อความแจ้งเตือน
        message = (
            f"ผู้ใช้งาน {order.user.first_name} ต้องการยกเลิกคำร้อง ID {order_id}\n"
            f"เหตุผล: {reason}"
        )

        # ส่งข้อความไปยังแอดมิน
        for user_id in admin_user_ids:
            try:
                line_bot_api.push_message(user_id, TextSendMessage(text=message))
            except Exception as e:
                print(f"เกิดข้อผิดพลาดในการส่งข้อความถึงผู้ใช้ {user_id}: {e}")



#ส่งการแจ้งเตือนไปยังผู้ใช้งานเมื่อเช็คเอ้าท์สินค้า
def notify_user(order_id):
    try:
        order = Order.objects.get(id=order_id)
        user_line = UserLine.objects.get(user=order.user)

        # ดึงรายการสินค้าที่ถูกเบิก
        items = order.items.all()  # Assuming `order.items` is the related name for OrderItems

        # สร้างข้อความรายการสินค้า
        items_list = "\n".join([f"- {item.product.product_name}: {item.quantity} {item.product.unit}" for item in items])

        # คำนวณจำนวนเงินรวม
        total_cost = sum(item.get_cost() for item in items)

        # message = f"{order.user.username} รายการเบิกวัสดุ เลขที่เบิก {order_id} ของคุณ ที่ต้องได้รับการอนุมัติ.."
        message = (
            f"{order.user.first_name} รายการเบิกวัสดุเลขที่เบิก {order_id} ของคุณที่ต้องได้รับการอนุมัติ..\n"
            f"รายการวัดสุที่เบิก:\n{items_list}"
            f"\nยอดเงินรวม: {total_cost} บาท"
        )
        print(message)
        line_bot_api.push_message(user_line.userId, TextSendMessage(text=message))
    except Order.DoesNotExist:
        print(f"ไม่มีคำร้อง ID {order_id}")
    except UserLine.DoesNotExist:
        print(f"ไม่มี UserLine สำหรับผู้ใช้งาน {order.user.first_name}")


#ส่งการแจ้งเตือนไปยังแอดมินเมื่อเช็คเอ้าท์สินค้า
def notify_admin(order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        print("ไม่พบคำสั่งซื้อ")
        return

    # ค้นหาผู้ใช้งานที่เป็น manager และ admin
    users_to_notify = MyUser.objects.filter(is_manager=True) | MyUser.objects.filter(is_admin=True)

    # ดึง Line User IDs ของผู้ใช้งานเหล่านี้
    admin_user_ids = []
    for user in users_to_notify:
        try:
            user_line = UserLine.objects.get(user=user)
            admin_user_ids.append(user_line.userId)
        except UserLine.DoesNotExist:
            print(f"ไม่มี Line ID สำหรับผู้ใช้ {user.username}")

    if not admin_user_ids:
        print("ไม่พบ Line ID สำหรับผู้ใช้ผู้ดูแลระบบ")
        return

    # ดึงรายการสินค้าที่ถูกเบิก
    items = order.items.all()  # Assuming `order.items` is the related name for OrderItems

    # สร้างข้อความรายการสินค้า
    items_list = "\n".join([
        f"- {item.product.product_name}: {item.quantity} {item.product.unit} ๆ ละ {item.price} บาท หมายเหตุ: {item.note}" 
        for item in items
    ])

    # คำนวณจำนวนเงินรวม
    total_cost = sum(item.get_cost() for item in items)

    # สร้างข้อความที่จะส่ง
    message = (
        f"คำร้องใหม่จากผู้ใช้งาน {order.user.first_name} เลขที่เบิก {order_id} ที่ต้องได้รับการอนุมัติ..\n"
        f"รายการวัสดุที่เบิก:\n{items_list}"
        f"\nยอดเงินรวม: {total_cost} บาท"
    )

    # ส่งข้อความไปยังผู้ใช้งานที่เป็น manager และ admin
    for user_id in admin_user_ids:
        try:
            line_bot_api.push_message(user_id, TextSendMessage(text=message))
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการส่งข้อความถึงผู้ใช้ {user_id}: {e}")



#ส่งการแจ้งเตือนไปยังผู้ใช้งานเมื่อมีการอนุมัติคำร้อง
def notify_user_approved(order_id):
    try:
        order = Order.objects.get(id=order_id)
        user_line = UserLine.objects.get(user=order.user)

        # ตรวจสอบว่า date_receive ไม่เป็น None
        if order.date_receive:
            # ตั้งค่า timezone ที่ต้องการ (เช่น Asia/Bangkok)
            timezone = pytz.timezone('Asia/Bangkok')
            order_date_receive_with_timezone = order.date_receive.astimezone(timezone)
            formatted_date = order_date_receive_with_timezone.strftime("%d/%m/%Y")
            formatted_time = order_date_receive_with_timezone.strftime("%H:%M")
        else:
            formatted_date = None
            formatted_time = None

        # ตรวจสอบค่า status
        if order.status:
            if order.date_receive:
                message = f"รายการเบิกวัสดุของคุณ {order.user.first_name} ID {order_id} ได้รับการอนุมัติแล้ว✅ รับวัสดุในวันที่ {formatted_date} 🕒 {formatted_time} น."
            else:
                message = f"รายการเบิกวัสดุของคุณ {order.user.first_name} ID {order_id} ได้รับการอนุมัติแล้ว✅"
        else:
            message = f"รายการเบิกวัสดุของคุณ {order.user.first_name} ID {order_id} ถูกปฏิเสธ!💔 หมายเหตุ {order.other}"

        line_bot_api.push_message(user_line.userId, TextSendMessage(text=message))
    except Order.DoesNotExist:
        print(f"ไม่มีคำร้อง ID {order_id}")
    except UserLine.DoesNotExist:
        print(f"ไม่มี UserLine สำหรับผู้ใช้งาน {order.user.username}")



# ส่งการแจ้งเตือนไปยังผู้ใช้งานเมื่อมีการยืนยันจ่ายวัสดุ 
def notify_user_pay_confirmed(order_id):
    try:
        order = Order.objects.get(id=order_id)
        user_line = UserLine.objects.get(user=order.user)

        # Check if order.date_receive is not None
        if order.date_receive:
            # Set timezone to the desired timezone (e.g., Asia/Bangkok)
            timezone = pytz.timezone('Asia/Bangkok')
            order_date_receive_with_timezone = order.date_receive.astimezone(timezone)

        if order.pay_item:
            if order.date_receive:
                formatted_date = order_date_receive_with_timezone.strftime("%d/%m/%Y")
                formatted_time = order_date_receive_with_timezone.strftime("%H:%M")
                message = f"รายการเบิกวัสดุของคุณ {order.user.first_name} ID {order_id} ได้รับการยืนยันจ่ายวัสดุแล้ว✅ กรุณากด ยืนยันการรับพัสดุ"
            else:
                message = f"รายการเบิกวัสดุของคุณ {order.user.first_name} ID {order_id} ได้รับการยืนยันจ่ายวัสดุแล้ว✅"
        else:
            message = f"รายการเบิกวัสดุของคุณ {order.user.first_name} ID {order_id} ยังไม่ได้รับการยืนยันจ่ายวัสดุ😓"

        line_bot_api.push_message(user_line.userId, TextSendMessage(text=message))
    except Order.DoesNotExist:
        print(f"ไม่มีคำร้อง ID {order_id}")
    except UserLine.DoesNotExist:
        print(f"ไม่มี UserLine สำหรับผู้ใช้งาน {order.user.username}")


# ส่งการแจ้งเตือนไปยังแอดมินเมื่อผู้ใช้ยืนยันรับพัสดุ
def notify_admin_receive_confirmation(order_id):
    try:
        order = Order.objects.get(id=order_id)
        admin_user_id = 'Ubb217fccfe04b1dbf5550e46661a8693'  # Replace with the actual Line user ID of the admin
        
        if order.confirm:
            message = f"{order.user.first_name} ได้ยืนยันรับพัสดุคำร้องเลขที่ {order_id} เรียบร้อยแล้ว. "
        else:
            message = f"คำร้องเลขที่ {order_id} ของ {order.user.first_name} ยังไม่ได้รับการยืนยันรับพัสดุ."
        
        line_bot_api.push_message(admin_user_id, TextSendMessage(text=message))
    except Order.DoesNotExist:
        print(f"ไม่มีคำร้อง ID {order_id}")