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

from django.utils.dateparse import parse_date
from datetime import datetime, timezone
line_bot_api = LineBotApi('p/7wo/1oBrhYYteqvWuGQQJz5AADd3pnSiyTJByIju6L6rT5fWsifmzRiD8YOoPHYZkSQHNMIcnAyjMq9ad3zjL4LHn4+C5PubjxDeGXrcXO5XIYd65jHw2slPVxQ7akCkzj0ZC+8MRIJ3oIBRpHLAdB04t89/1O/w1cDnyilFU=')

# @csrf_exempt
# def linebot(request):
#     print(request.method)

#     if request.method == 'POST':
#         try:
#             body = request.body.decode('utf-8')
#             body = json.loads(body)
#             events = body.get('events', [])

#             if events:
#                 event = events[0]
#                 text = event.get('message', {}).get('text', '')

#                 if text.startswith('ผูกบัญชี'):
#                     a = text.split()
#                     if len(a) == 2:
#                         username = a[1]
#                         user = MyUser.objects.filter(username=username).first()

#                         if user:
#                             line = UserLine.objects.filter(user=user).first()
#                             userId = event.get('source', {}).get('userId', '')
#                             print(user)
#                             print(userId)

#                             if not line:
#                                 line = UserLine(user=user, userId=userId)
#                                 line.save()

#                                 # ส่งข้อความแจ้งเตือนผู้ใช้
#                                 line_bot_api.push_message(userId, TextSendMessage(text='ผูกบัญชีสำเร็จ✅'))

#                             else:
#                                 line.userId = userId
#                                 line.save()

#                                 # ส่งข้อความแจ้งเตือนผู้ใช้ (กรณีอัพเดตการผูกบัญชี)
#                                 line_bot_api.push_message(userId, TextSendMessage(text='อัพเดตการผูกบัญชีสำเร็จ✅'))
#                         else:
#                             # ส่งข้อความแจ้งเตือนถ้า username ไม่ถูกต้อง
#                             userId = event.get('source', {}).get('userId', '')
#                             line_bot_api.push_message(userId, TextSendMessage(text='⚠ Username ไม่ถูกต้อง❗\nกรุณาตรวจสอบและลองใหม่อีกครั้ง'))
#                     else:
#                         # ส่งข้อความแจ้งเตือนถ้ามีการป้อนข้อมูลไม่ครบ
#                         userId = event.get('source', {}).get('userId', '')
#                         line_bot_api.push_message(userId, TextSendMessage(text='⚠ กรุณาพิมพ์คำว่า "ผูกบัญชี ตามด้วย Username ของคุณค่ะ"'))
#                 else:
#                     # ส่งข้อความแจ้งเตือนว่าข้อความไม่ถูกต้อง
#                     userId = event.get('source', {}).get('userId', '')
#                     line_bot_api.push_message(userId, TextSendMessage(text='⚠ ข้อความไม่ถูกต้อง❗\nกรุณาพิมพ์คำว่า "ผูกบัญชี ตามด้วย Username ของคุณค่ะ"'))

#         except json.JSONDecodeError as e:
#             print(f"JSON Decode Error: {e}")

#     return render(request, "home_page.html")


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
                userId = event.get('source', {}).get('userId', '')

                # ตรวจสอบว่าผู้ใช้ได้ผูกบัญชีหรือยัง
                line_user = UserLine.objects.filter(userId=userId).first()

                if not line_user:
                    line_bot_api.push_message(userId, TextSendMessage(text='⚠ คุณยังไม่ได้ผูกบัญชีกับระบบ กรุณาผูกบัญชีก่อน'))
                    return

                user = line_user.user  # ดึงข้อมูลผู้ใช้ที่ผูกกับ Line ID นี้

                # ผูกบัญชี
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

                # ยืนยันรับวัสดุ
                elif text.startswith('ยืนยันรับวัสดุID'):
                    command_parts = text.split()
                    
                    print(f"Command Parts: {command_parts}")  # ดีบักเพื่อดูคำสั่งที่แยกออก
                    if len(command_parts) >= 3:  # ต้องมี ID และชื่อผู้รับวัสดุ
                        order_id = command_parts[1]  # แก้ไขจาก command_parts[1] เป็น command_parts[2]
                        name_sign = ' '.join(command_parts[2:])  # รวมชื่อผู้รับวัสดุจากคำที่ 3 เป็นต้นไป
                        print(f"Order ID: {order_id}, Name Sign: {name_sign}")  # ดีบักค่า ID และชื่อ

                        order = Order.objects.filter(id=order_id).first()

                        if order:
                            if not order.confirm:  # ตรวจสอบว่าออเดอร์ยังไม่ได้รับการยืนยัน
                                order.confirm = True  # ตั้งค่าสถานะการยืนยันรับวัสดุ
                                order.name_sign = name_sign  # บันทึกชื่อผู้รับวัสดุ
                                # order.date_received = timezone.now()  # บันทึกวันที่ได้รับวัสดุ
                                order.save()
                                print(f"Order ID: {order_id}, Name Sign: {name_sign}, Confirm: {order.confirm}")

                            # ส่งการแจ้งเตือนให้ผู้ใช้
                                line_bot_api.push_message(userId, TextSendMessage(text=f'ยืนยันรับวัสดุสำหรับคำร้อง ID {order_id} สำเร็จ ✅'))
                            else:
                                line_bot_api.push_message(userId, TextSendMessage(text='⚠ คำร้องนี้ได้รับการยืนยันแล้ว'))
                        else:
                            line_bot_api.push_message(userId, TextSendMessage(text='⚠ ไม่พบคำร้องนี้'))
                    else:
                        line_bot_api.push_message(userId, TextSendMessage(text='⚠ กรุณาพิมพ์ "ยืนยันรับวัสดุID [order_id] [ชื่อผู้รับวัสดุ]"'))


                # ตรวจสอบสิทธิ์ว่าผู้ใช้มีสิทธิ์เป็น is_manager หรือ is_admin
                elif user.is_manager or user.is_admin:
                    # อนุมัติคำร้อง
                    # อนุมัติคำร้อง
                    if text.startswith('อนุมัติคำร้อง'):
                        command_parts = text.split()
                        
                        if len(command_parts) >= 3:
                            order_id = command_parts[1]
                            date_receive = command_parts[2]

                            # ตรวจสอบว่ามีการระบุเวลา (HH:MM) หรือไม่
                            if len(command_parts) >= 4 and ":" in command_parts[3]:
                                time_receive = command_parts[3]
                                other = ' '.join(command_parts[4:]) if len(command_parts) > 4 else None
                            else:
                                time_receive = None
                                other = ' '.join(command_parts[3:]) if len(command_parts) > 3 else None

                            order = Order.objects.filter(id=order_id).first()

                            if order:
                                try:
                                    # แปลงวันที่
                                    parsed_date = datetime.strptime(date_receive, '%Y-%m-%d')

                                    # ถ้ามีการระบุเวลา ให้บันทึกเวลา
                                    if time_receive:
                                        parsed_time = datetime.strptime(time_receive, '%H:%M').time()
                                        order.date_receive = datetime.combine(parsed_date, parsed_time)
                                    else:
                                        order.date_receive = datetime.combine(parsed_date, datetime.min.time())  # ถ้าไม่มีเวลาจะใช้เวลาเริ่มต้น

                                    order.status = True  # อนุมัติ
                                    order.other = other  # บันทึกหมายเหตุ (ถ้ามี)
                                    order.save()

                                    # ส่งการแจ้งเตือนไปยังผู้ใช้งานที่ทำคำร้อง
                                    notify_user_approved(order.id)  # เรียกใช้ฟังก์ชันเพื่อแจ้งเตือน

                                    # ส่งการแจ้งเตือนกลับไปยังผู้อนุมัติ
                                    line_bot_api.push_message(userId, TextSendMessage(text=f'อนุมัติคำร้อง ID {order_id} สำเร็จ ✅'))

                                except ValueError:
                                    line_bot_api.push_message(userId, TextSendMessage(text='⚠ รูปแบบวันที่หรือเวลาไม่ถูกต้อง โปรดใช้รูปแบบ YYYY-MM-DD หรือ YYYY-MM-DD HH:MM'))
                            else:
                                line_bot_api.push_message(userId, TextSendMessage(text='⚠ ไม่พบคำร้องนี้'))
                        else:
                            line_bot_api.push_message(userId, TextSendMessage(text='⚠ กรุณาพิมพ์ "อนุมัติคำร้อง [order_id] [วันที่รับวัสดุ] [เวลา] [หมายเหตุ]"'))

                    # ปฏิเสธคำร้อง
                    elif text.startswith('ปฏิเสธคำร้อง'):
                        command_parts = text.split()
                        if len(command_parts) >= 2:
                            order_id = command_parts[1]
                            other = ' '.join(command_parts[2:]) if len(command_parts) > 2 else None

                            order = Order.objects.filter(id=order_id).first()

                            if order:
                                order.status = False  # ปฏิเสธ
                                order.other = other
                                order.save()

                                # ส่งการแจ้งเตือนไปยังผู้ใช้งานที่ทำคำร้อง
                                notify_user_approved(order.id)  # เรียกใช้ฟังก์ชันเพื่อแจ้งเตือน

                                # ส่งการแจ้งเตือนให้แอดมิน
                                line_bot_api.push_message(userId, TextSendMessage(text=f'ปฏิเสธคำร้อง ID {order_id} สำเร็จ ❌'))
                            else:
                                line_bot_api.push_message(userId, TextSendMessage(text='⚠ ไม่พบคำร้องนี้'))
                        else:
                            line_bot_api.push_message(userId, TextSendMessage(text='⚠ กรุณาพิมพ์ "ปฏิเสธคำร้อง [order_id] [หมายเหตุ]"'))
                    
                    # จ่ายวัสดุแล้ว
                    elif text.startswith('จ่ายวัสดุแล้วID'):
                        command_parts = text.split()
                        
                        if len(command_parts) >= 2:
                            order_id = command_parts[1]
                            order = Order.objects.filter(id=order_id).first()

                            if order:
                                order.pay_item = True  # ยืนยันว่าจ่ายวัสดุแล้ว
                                order.save()

                                # ส่งการแจ้งเตือนไปยังผู้ใช้งานที่ทำคำร้อง
                                # notify_user_pay_confirmed(order.id)

                                # ส่งการแจ้งเตือนไปยังผู้ใช้งานที่ทำการจองวัสดุ
                                line_bot_api.push_message(userId, TextSendMessage(text=f'จ่ายวัสดุสำหรับคำร้อง ID {order_id} สำเร็จ ✅'))
                            else:
                                line_bot_api.push_message(userId, TextSendMessage(text='⚠ ไม่พบคำร้องนี้'))
                        else:
                            line_bot_api.push_message(userId, TextSendMessage(text='⚠ กรุณาพิมพ์ "จ่ายวัสดุแล้วID [order_id]"'))

                else:
                    line_bot_api.push_message(userId, TextSendMessage(text='⚠ คุณไม่มีสิทธิ์ในการดำเนินการนี้'))
                    
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")

    return render(request, "home_page.html")




# def notify_admin_cancel(order_id, reason):
#     order = Order.objects.filter(id=order_id).first()
#     if order:
#         # ค้นหาผู้ใช้งานที่เป็น manager และ admin
#         users_to_notify = MyUser.objects.filter(is_manager=True) | MyUser.objects.filter(is_admin=True)

#         # ดึง Line User IDs ของผู้ใช้งานเหล่านี้
#         admin_user_ids = []
#         for user in users_to_notify:
#             try:
#                 user_line = UserLine.objects.get(user=user)
#                 admin_user_ids.append(user_line.userId)
#             except UserLine.DoesNotExist:
#                 print(f"ไม่มี Line ID สำหรับผู้ใช้ {user.username}")

#         # สร้างข้อความแจ้งเตือน
#         message = (
#             f"ผู้ใช้งาน {order.user.first_name} ต้องการยกเลิกคำร้อง ID {order_id}\n"
#             f"เหตุผล: {reason}"
#         )

#         # ส่งข้อความไปยังแอดมิน
#         for user_id in admin_user_ids:
#             try:
#                 line_bot_api.push_message(user_id, TextSendMessage(text=message))
#             except Exception as e:
#                 print(f"เกิดข้อผิดพลาดในการส่งข้อความถึงผู้ใช้ {user_id}: {e}")



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
                message = f"รายการเบิกวัสดุของ ID {order_id} ของคุณ ได้รับการอนุมัติแล้ว✅ รับวัสดุในวันที่ {formatted_date} 🕒 {formatted_time} น."
                # message = f"รายการเบิกวัสดุของคุณ {order.user.first_name} ID {order_id} ได้รับการอนุมัติแล้ว✅ รับวัสดุในวันที่ {formatted_date} 🕒 {formatted_time} น."
            else:
                message = f"รายการเบิกวัสดุของ ID {order_id} ของคุณ ได้รับการอนุมัติแล้ว✅"
        else:
            message = f"รายการเบิกวัสดุของ ID {order_id} ของคุณ ถูกปฏิเสธ!💔 หมายเหตุ : {order.other}"

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
                # message = f"รายการเบิกวัสดุของคุณ {order.user.first_name} ID {order_id} ได้รับการยืนยันจ่ายวัสดุแล้ว✅ กรุณากด ยืนยันการรับพัสดุ"
                message = f"คุณได้รับการอนุมัติ จ่ายวัสดุแล้ว✅ กรุณากด ยืนยันการรับวัสดุ"
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
            message = f"{order.user.first_name} ได้ยืนยันรับวัสดุคำร้องเลขที่ {order_id} เรียบร้อยแล้ว. "
        else:
            message = f"คำร้องเลขที่ {order_id} ของ {order.user.first_name} ยังไม่ได้รับการยืนยันรับวัสดุ."
        
        line_bot_api.push_message(admin_user_id, TextSendMessage(text=message))
    except Order.DoesNotExist:
        print(f"ไม่มีคำร้อง ID {order_id}")