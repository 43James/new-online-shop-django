# Create your views here.
import traceback
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import pytz
from accounts.models import MyUser
from assets.models import OrderAssetLoan
from orders.models import Issuing, Order, OutOfStockNotification
from shop.models import Product
from .models import UserLine, UserLine_Asset
from linebot import LineBotApi
from linebot.models import TextSendMessage
import json
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from datetime import datetime
from django.utils import timezone
from linebot.exceptions import LineBotApiError
import locale
import pytz


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
                userId = event.get('source', {}).get('userId', '')
                text = event.get('message', {}).get('text', '')

                # ตรวจสอบการผูกบัญชี
                line = UserLine.objects.filter(userId=userId).first()

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
                        line_bot_api.push_message(userId, TextSendMessage(text='⚠ กรุณาพิมพ์คำว่า \n"ผูกบัญชี ตามด้วย Username ของคุณค่ะ"'))

                # แจ้งเตือนผู้ใช้ถ้ายังไม่ผูกบัญชี
                elif not line:
                    line_bot_api.push_message(userId, TextSendMessage(text='⚠ กรุณาผูกบัญชีของคุณก่อนใช้งาน\nใช้คำสั่ง "ผูกบัญชี [Username]"'))
                    # return HttpResponse(status=200)

                
                # ยืนยันรับวัสดุ
                elif text.startswith('รับวัสดุแล้วID'):
                    command_parts = text.split()
                    
                    print(f"Command Parts: {command_parts}")  # ดีบักเพื่อดูคำสั่งที่แยกออก
                    if len(command_parts) >= 2:  # ต้องมี ID ของคำร้องเท่านั้น
                        order_id = command_parts[1]  # ใช้ ID เป็นคำที่ 1

                        try:
                            # กำหนดวันที่และเวลาปัจจุบัน
                            date_time_received = timezone.now()
                            print(f"Current Date and Time: {date_time_received}")  # ดีบักเพื่อดูวันที่และเวลาปัจจุบัน

                            # ดึงข้อมูลออเดอร์
                            order = Order.objects.filter(id=order_id).first()

                            if order:
                                if not order.confirm:  # ตรวจสอบว่าออเดอร์ยังไม่ได้รับการยืนยัน
                                    order.confirm = True  # ตั้งค่าสถานะการยืนยันรับวัสดุ

                                    # ใช้ชื่อผู้ใช้งานจากข้อมูลออเดอร์ (first_name)
                                    name_sign = order.user.get_first_name()
                                    order.name_sign = name_sign  # บันทึกชื่อผู้รับวัสดุ
                                    order.date_received = date_time_received  # บันทึกวันที่และเวลารับวัสดุ

                                    # ดีบักก่อนบันทึก
                                    print(f"Saving Order ID: {order.id}, Name Sign: {name_sign}, Date Received: {date_time_received}")
                                    
                                    order.save()

                                    # ตรวจสอบว่าอัปเดตสำเร็จหรือไม่
                                    if order.date_received:
                                        print(f"Date Received successfully saved: {order.date_received}")
                                    
                                    # ส่งการแจ้งเตือนให้ผู้ใช้งาน
                                    line_bot_api.push_message(userId, TextSendMessage(text=f'ยืนยันรับวัสดุคำร้อง ID {order_id} สำเร็จ✅'))

                                    # ส่งการแจ้งเตือนให้แอดมิน
                                    notify_admin_receive_confirmation(order.id)

                                else:
                                    line_bot_api.push_message(userId, TextSendMessage(text='⚠ คำร้องนี้ได้รับการยืนยันแล้ว'))
                            else:
                                line_bot_api.push_message(userId, TextSendMessage(text='⚠ ไม่พบคำร้องนี้'))

                        except Exception as e:
                            print(f"Error: {e}")
                            line_bot_api.push_message(userId, TextSendMessage(text='⚠ เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง'))
                    else:
                        line_bot_api.push_message(userId, TextSendMessage(text='⚠ กรุณาพิมพ์ \n"รับวัสดุแล้วID [เลขที่คำร้อง]"'))



                # เช็คสถานะ
                elif text.startswith('เช็คสถานะID'):
                    command_parts = text.split()

                    if len(command_parts) == 2:
                        order_id = command_parts[1]
                        order = Order.objects.filter(id=order_id).first()

                        if order:
                            # ดึงข้อมูลผู้เบิกวัสดุ
                            user_name = order.user.get_full_name() if order.user else "ไม่พบข้อมูลผู้เบิก"
                            
                            # ดึงรายการวัสดุที่เบิกจากตาราง Issuing
                            issuing_items = Issuing.objects.filter(order=order)
                            product_list = '\n'.join([f"สินค้า: {item.product.product_name}, จำนวน: {item.quantity}, ราคา: {item.price} บาท" for item in issuing_items])

                            # เตรียมข้อความเพื่อแสดงข้อมูลคำร้อง
                            status_message = f"คำร้อง ID: {order_id}\n"
                            status_message += f"ชื่อผู้เบิก: {user_name}\n\n"
                            status_message += f"รายการวัสดุที่เบิก:\n{product_list}\n\n"
                            # สถานะออเดอร์
                            if order.status is None:
                                status_message += "สถานะออเดอร์: ยังไม่ได้รับการยืนยัน\n\n"
                            elif order.status is False:
                                status_message += "สถานะออเดอร์: ถูกปฏิเสธ❌\n\n"
                            else:  # order.status is True
                                status_message += "สถานะออเดอร์: อนุมัติแล้ว✅\n\n"
                            status_message += f"วันที่นัดรับพัสดุ: {order.date_receive.strftime('%d-%m-%Y') if order.date_receive else 'ยังไม่มีการระบุ'}\n"
                            status_message += f"วันที่รับพัสดุ: {order.date_received.strftime('%d-%m-%Y') if order.date_received else 'ยังไม่มีการระบุ'}\n\n"
                            status_message += f"สถานะการจ่ายวัสดุ: {'จ่ายแล้ว' if order.pay_item else 'ยังไม่ได้ยืนยันจ่ายวัสดุ'}\n"
                            status_message += f"สถานะการรับวัสดุ: {'ยืนยันแล้ว✅' if order.confirm else 'ยังไม่ได้ยืนยันรับวัสดุ'}\n"
                            status_message += f"ชื่อผู้รับวัสดุ: {order.name_sign if order.name_sign else 'ยังไม่มีการระบุ'}\n\n"
                            status_message += f"หมายเหตุ: {order.other if order.other else 'ไม่มีหมายเหตุ'}\n"

                            # ส่งข้อมูลสถานะกลับไปยังผู้ใช้งาน
                            line_bot_api.push_message(userId, TextSendMessage(text=status_message))
                        else:
                            # ส่งข้อความแจ้งเตือนถ้าไม่พบคำร้อง
                            line_bot_api.push_message(userId, TextSendMessage(text='⚠ ไม่พบคำร้องนี้'))
                    else:
                        # ส่งข้อความแจ้งเตือนถ้าพิมพ์คำสั่งไม่ถูกต้อง
                        line_bot_api.push_message(userId, TextSendMessage(text='⚠ กรุณาพิมพ์ \n"เช็คสถานะID [เลขที่คำร้อง]"'))


                # ตรวจสอบสิทธิ์ว่าผู้ใช้มีสิทธิ์เป็น is_manager หรือ is_admin
                user = line.user  # ดึงข้อมูลผู้ใช้จากการผูกบัญชี
                if user.is_manager or user.is_admin:
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
                                if order.status:  # ตรวจสอบสถานะก่อนอนุมัติ
                                    line_bot_api.push_message(userId, TextSendMessage(text='⚠ คำร้องนี้ได้รับการอนุมัติแล้ว'))

                                else:  # ตรวจสอบสถานะก่อนอนุมัติ
                                    try:
                                        # แปลงวันที่
                                        parsed_date = datetime.strptime(date_receive, '%d-%m-%Y')

                                        # ถ้ามีการระบุเวลา ให้บันทึกเวลา
                                        if time_receive:
                                            parsed_time = datetime.strptime(time_receive, '%H:%M').time()
                                            order.date_receive = datetime.combine(parsed_date, parsed_time)
                                        else:
                                            order.date_receive = datetime.combine(parsed_date, datetime.min.time())  # ถ้าไม่มีเวลาจะใช้เวลาเริ่มต้น

                                        order.status = True  # อนุมัติ
                                        order.other = other  # บันทึกหมายเหตุ (ถ้ามี)
                                        order.save()

                                        # ส่งการแจ้งเตือนกลับไปยังผู้อนุมัติ
                                        line_bot_api.push_message(userId, TextSendMessage(text=f'อนุมัติคำร้อง ID {order_id} สำเร็จ ✅'))

                                        # ส่งการแจ้งเตือนไปยังผู้ใช้งานที่ทำคำร้อง
                                        notify_user_approved(order.id)  # เรียกใช้ฟังก์ชันเพื่อแจ้งเตือน
                                        notify_admin_order_status(order.id)

                                    except ValueError:
                                        line_bot_api.push_message(userId, TextSendMessage(text='⚠ รูปแบบวันที่หรือเวลาไม่ถูกต้อง โปรดใช้รูปแบบ วัน-เดือน-ปี หรือ วัน-เดือน-ปี HH:MM'))
                                
                            else:
                                line_bot_api.push_message(userId, TextSendMessage(text='⚠ ไม่พบคำร้องนี้'))
                        else:
                            line_bot_api.push_message(userId, TextSendMessage(text='⚠ กรุณาพิมพ์ \n"อนุมัติคำร้อง [เลขที่คำร้อง] [วันที่รับวัสดุ] [เวลา] [หมายเหตุ]"'))


                    # ปฏิเสธคำร้อง
                    elif text.startswith('ปฏิเสธคำร้อง'):
                        command_parts = text.split()
                        if len(command_parts) >= 2:
                            order_id = command_parts[1]
                            other = ' '.join(command_parts[2:]) if len(command_parts) > 2 else None

                            order = Order.objects.filter(id=order_id).first()

                            if order:
                                if order.status == False:  # ตรวจสอบว่าคำร้องนี้ถูกปฏิเสธแล้วหรือไม่
                                    line_bot_api.push_message(userId, TextSendMessage(text='⚠ คำร้องนี้ถูกปฏิเสธแล้ว'))
                                else:
                                    order.status = False  # ปฏิเสธ
                                    order.other = other
                                    order.save()

                                    # ส่งการแจ้งเตือนให้แอดมิน
                                    line_bot_api.push_message(userId, TextSendMessage(text=f'ปฏิเสธคำร้อง ID {order_id} สำเร็จ ❌'))

                                    # คืนจำนวนสินค้ากลับไปยังสต๊อก
                                    for item in order.items.all():  # assuming `items` is a related name for Issuing
                                        product = item.product
                                        product.quantityinstock += item.quantity  # เพิ่มจำนวนวัสดุกลับไปในสต๊อก
                                        product.save()
                                        print(f"Restored {item.quantity} of {product.product_name} to stock.")

                                        # คืนจำนวนสินค้าที่รับเข้าใน Receiving
                                        receiving = item.receiving
                                        receiving.quantity += item.quantity  # เพิ่มจำนวนใน Receiving
                                        receiving.save()
                                        print(f"Restored {item.quantity} to receiving ID {receiving.id}.")

                                    # ส่งการแจ้งเตือนไปยังผู้ใช้งานที่ทำคำร้อง
                                    notify_user_approved(order.id)  # เรียกใช้ฟังก์ชันเพื่อแจ้งเตือน
                                    notify_admin_order_status(order.id)
                            else:
                                line_bot_api.push_message(userId, TextSendMessage(text='⚠ ไม่พบคำร้องนี้'))
                        else:
                            line_bot_api.push_message(userId, TextSendMessage(text='⚠ กรุณาพิมพ์ \n"ปฏิเสธคำร้อง [เลขที่คำร้อง] [หมายเหตุ]"'))


                    # จ่ายวัสดุแล้ว
                    elif text.startswith('จ่ายวัสดุแล้วID'):
                        command_parts = text.split()

                        if len(command_parts) == 2:
                            order_id = command_parts[1]
                            order = Order.objects.filter(id=order_id).first()

                            if order:
                                if not order.pay_item:  # ตรวจสอบว่ายังไม่ได้จ่ายวัสดุก่อน
                                    order.pay_item = True  # ยืนยันว่าจ่ายวัสดุแล้ว
                                    order.save()

                                    # ส่งการแจ้งเตือนไปยังผู้ใช้งานที่ทำคำร้อง
                                    notify_user_pay_confirmed(order.id)

                                    # ส่งการแจ้งเตือนไปยังผู้อนุมัติ
                                    line_bot_api.push_message(userId, TextSendMessage(text=f'จ่ายวัสดุสำหรับคำร้อง ID {order_id} สำเร็จ ✅'))
                                else:
                                    line_bot_api.push_message(userId, TextSendMessage(text='⚠ เจ้าหน้าที่ได้จ่ายวัสดุคำร้องนี้แล้ว'))
                            else:
                                line_bot_api.push_message(userId, TextSendMessage(text='⚠ ไม่พบคำร้องนี้'))
                        else:
                            line_bot_api.push_message(userId, TextSendMessage(text='⚠ กรุณาพิมพ์ \n"จ่ายวัสดุแล้วID [เลขที่คำร้อง]"'))
                # else:
                #     line_bot_api.push_message(userId, TextSendMessage(text='⚠ คุณไม่มีสิทธิ์ในการดำเนินการนี้'))

        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
    return HttpResponse(status=200)



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
            # f"\nยอดเงินรวม: {total_cost} บาท"
        )
        print(message)
        line_bot_api.push_message(user_line.userId, TextSendMessage(text=message))
    except Order.DoesNotExist:
        print(f"ไม่มีคำร้อง ID {order_id}")
    except UserLine.DoesNotExist:
        print(f"ไม่มี UserLine สำหรับผู้ใช้งาน {order.user.first_name}")
    except LineBotApiError as e:
        print(f"เกิดข้อผิดพลาดในการส่งข้อความผ่าน Line: {str(e)}")
        # แจ้งเตือนเมื่อไม่สามารถส่งข้อความผ่าน Line ได้
        if e.status_code == 429:  # กรณีที่จำนวนการส่งข้อความเกินลิมิต
            print("ถึงขีดจำกัดการส่งข้อความในเดือนนี้")
        else:
            print(f"ข้อผิดพลาดที่ไม่รู้จัก: {str(e)}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดทั่วไป: {str(e)}")



#ส่งการแจ้งเตือนไปยังแอดมินเมื่อเช็คเอ้าท์สินค้า
def notify_admin(request, order_id):
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
        messages.warning(request, "ไม่พบ Line ID สำหรับผู้ใช้ผู้ดูแลระบบ")
        return

    # ดึงรายการสินค้าที่ถูกเบิก
    items = order.items.all()

    # สร้างข้อความรายการสินค้า
    items_list = "\n".join([
        f"- {item.product.product_name}: {item.quantity} {item.product.unit} ๆ ละ {item.price} บาท หมายเหตุ: {item.note}" 
        for item in items
    ])

    # คำนวณจำนวนเงินรวม
    total_cost = sum(item.get_cost() for item in items)

    # สร้างข้อความที่จะส่ง
    message = (
        f"คำร้องใหม่จาก {order.user.first_name} เลขที่เบิก {order_id} ที่ต้องได้รับการอนุมัติ..\n"
        f"รายการวัสดุที่เบิก:\n{items_list}"
        f"\nยอดเงินรวม: {total_cost} บาท"
    )

    # ส่งข้อความไปยังผู้ใช้งานที่เป็น manager และ admin ในคราวเดียว
    try:
        line_bot_api.multicast(admin_user_ids, TextSendMessage(text=message))
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการส่งข้อความถึงผู้ใช้: {e}")
        # เพิ่มการแจ้งเตือนธรรมดาแทนการให้แสดงเออเร่อ
        messages.warning(request, "ไม่สามารถส่งข้อความแจ้งเตือนผ่าน Line ได้ เนื่องจากคุณถึงจำนวนจำกัดของเดือนแล้ว")




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
                message = f"รายการเบิกวัสดุID {order_id} ของคุณ ได้รับการอนุมัติแล้ว✅ รับวัสดุในวันที่ {formatted_date} 🕒 {formatted_time} น."
                # message = f"รายการเบิกวัสดุของคุณ {order.user.first_name} ID {order_id} ได้รับการอนุมัติแล้ว✅ รับวัสดุในวันที่ {formatted_date} 🕒 {formatted_time} น."
            else:
                message = f"รายการเบิกวัสดุID {order_id} ของคุณ ได้รับการอนุมัติแล้ว✅"
        else:
            message = f"รายการเบิกวัสดุID {order_id} ของคุณ ถูกปฏิเสธ!💔 หมายเหตุ : {order.other}"

        line_bot_api.push_message(user_line.userId, TextSendMessage(text=message))
    except Order.DoesNotExist:
        print(f"ไม่มีคำร้อง ID {order_id}")
    except UserLine.DoesNotExist:
        print(f"ไม่มี UserLine สำหรับผู้ใช้งาน {order.user.username}")
    except LineBotApiError as e:
        print(f"เกิดข้อผิดพลาดในการส่งข้อความผ่าน Line: {str(e)}")
        # แจ้งเตือนเมื่อไม่สามารถส่งข้อความผ่าน Line ได้
        if e.status_code == 429:  # กรณีที่จำนวนการส่งข้อความเกินลิมิต
            print("ถึงขีดจำกัดการส่งข้อความในเดือนนี้")
        else:
            print(f"ข้อผิดพลาดที่ไม่รู้จัก: {str(e)}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดทั่วไป: {str(e)}")



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
    except LineBotApiError as e:
        print(f"เกิดข้อผิดพลาดในการส่งข้อความผ่าน Line: {str(e)}")
        # แจ้งเตือนเมื่อไม่สามารถส่งข้อความผ่าน Line ได้
        if e.status_code == 429:  # กรณีที่จำนวนการส่งข้อความเกินลิมิต
            print("ถึงขีดจำกัดการส่งข้อความในเดือนนี้")
        else:
            print(f"ข้อผิดพลาดที่ไม่รู้จัก: {str(e)}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดทั่วไป: {str(e)}")
    


# ส่งการแจ้งเตือนไปยังแอดมินเมื่อผู้ใช้ยืนยันรับพัสดุ
def notify_admin_receive_confirmation(order_id):
    try:
        order = Order.objects.get(id=order_id)
        admin_user_ids = UserLine.objects.filter(
            user__is_manager=True
        ).values_list('userId', flat=True)
        
        admin_user_ids = set(admin_user_ids)  # ใช้ set เพื่อลดความซ้ำซ้อน
        admin_user_ids.update(
            UserLine.objects.filter(user__is_admin=True).values_list('userId', flat=True)
        )

        if order.confirm:
            message = f"{order.user.first_name} ยืนยันรับวัสดุ คำร้องID {order_id} เรียบร้อยแล้ว."
        else:
            message = f"คำร้องเลขที่ {order_id} ของ {order.user.first_name} ยังไม่ได้รับการยืนยันรับวัสดุ."
        
        # ส่งข้อความไปยังแต่ละ admin_user_id
        for admin_user_id in admin_user_ids:
            try:
                line_bot_api.push_message(admin_user_id, TextSendMessage(text=message))
                print(f"ส่งข้อความถึง {admin_user_id} สำเร็จ")
            except LineBotApiError as e:
                print(f"ส่งข้อความไม่สำเร็จถึง {admin_user_id}: {e.status_code} {e.error.message}")
    
    except Order.DoesNotExist:
        print(f"ไม่มีคำร้อง ID {order_id}")
    except LineBotApiError as e:
        print(f"เกิดข้อผิดพลาดในการส่งข้อความผ่าน Line: {str(e)}")
        if e.status_code == 429:  # กรณีที่จำนวนการส่งข้อความเกินลิมิต
            print("ถึงขีดจำกัดการส่งข้อความในเดือนนี้")
        else:
            print(f"ข้อผิดพลาดที่ไม่รู้จัก: {str(e)}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดทั่วไป: {str(e)}")




# ส่งการแจ้งเตือนไปยังผู้จัดการคลังหรือมีการอนุมัติ/ปฏิเสธคำร้องเพื่อเตรียมวัสดุ
def notify_admin_order_status(order_id):
    try:
        order = Order.objects.get(id=order_id)
        
        # ดึง userId ของผู้ใช้งานที่เป็น manager และ admin
        admin_user_ids = list(UserLine.objects.filter(
            user__is_warehouse_manager=True
        ).values_list('userId', flat=True)) + list(
            UserLine.objects.filter(user__is_admin=True).values_list('userId', flat=True)
        )

        if not admin_user_ids:
            print("ไม่พบ Line ID สำหรับผู้ใช้ผู้ดูแลระบบหรือผู้จัดการ")
            return

        # สร้างข้อความที่จะส่ง
        message = f"คำร้องเลขที่ {order_id} ของ {order.user.first_name} "
        
        # ตรวจสอบสถานะการอนุมัติคำร้องและปรับข้อความใน message
        if order.status is True:
            if order.date_receive:
                # ตรวจสอบและจัดการ timezone
                timezone = pytz.timezone('Asia/Bangkok')
                order_date_receive_with_timezone = order.date_receive.astimezone(timezone)
                formatted_date = order_date_receive_with_timezone.strftime("%d/%m/%Y")
                formatted_time = order_date_receive_with_timezone.strftime("%H:%M")
                
                # เพิ่มข้อความที่มีวันที่และเวลา
                message += f"ได้รับการอนุมัติแล้ว ✅ \nเจ้าหน้าที่เตรียมส่งมอบวัสดุในวันที่ {formatted_date} เวลา {formatted_time}."
            else:
                # ถ้าไม่มีวันที่รับ
                message += f"ได้รับการอนุมัติแล้ว ✅ \nแต่ยังไม่ได้กำหนดวันส่งมอบ."
        
        elif order.status is False:
            message += f"ถูกปฏิเสธ ❌"
        
        elif order.status is None:
            message += f"ยังไม่ได้รับการยืนยัน"
        
        # ส่งการแจ้งเตือนให้ผู้ใช้งานหลายคนในครั้งเดียว
        line_bot_api.multicast(admin_user_ids, TextSendMessage(text=message))
    
    except Order.DoesNotExist:
        print(f"ไม่มีคำร้อง ID {order_id}")
    except LineBotApiError as e:
        print(f"เกิดข้อผิดพลาดในการส่งข้อความผ่าน Line: {str(e)}")
        # แจ้งเตือนเมื่อไม่สามารถส่งข้อความผ่าน Line ได้
        if e.status_code == 429:  # กรณีที่จำนวนการส่งข้อความเกินลิมิต
            print("ถึงขีดจำกัดการส่งข้อความในเดือนนี้")
        else:
            print(f"ข้อผิดพลาดที่ไม่รู้จัก: {str(e)}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดทั่วไป: {str(e)}")



# ฟังก์ชันส่งการแจ้งเตือนจ่ายวัสดุแล้วไปยังผู้ใช้งาน
def send_receive_confirmation(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)
        user_line = get_object_or_404(UserLine, user=order.user)

        if order.pay_item:
            if order.date_receive:
                timezone = pytz.timezone('Asia/Bangkok')
                order_date_receive_with_timezone = order.date_receive.astimezone(timezone)
                formatted_date = order_date_receive_with_timezone.strftime("%d/%m/%Y")
                formatted_time = order_date_receive_with_timezone.strftime("%H:%M")
                message = (
                    f"{order.user.first_name} เจ้าหน้าที่พัสดุจ่ายวัสดุแล้ว กรุณากดยืนยันการรับวัสดุ "
                )
            else:
                message = f"{order.user.first_name} เจ้าหน้าที่พัสดุจ่ายวัสดุแล้ว กรุณายืนยันการรับวัสดุ"
        else:
            message = "รายการของคุณยังไม่ได้รับการยืนยันจ่ายวัสดุ😓"

        # ตรวจสอบ User ID และ Message ก่อนส่ง
        print(f"Sending to User ID: {user_line.userId}")
        print(f"Message: {message}")

        line_bot_api.push_message(user_line.userId, TextSendMessage(text=message))
        print("ส่งการแจ้งเตือนแล้ว")
        messages.success(request, 'การแจ้งเตือนถูกส่งไปยังผู้ใช้แล้ว')

    except LineBotApiError as e:
        messages.error(request, f"เกิดข้อผิดพลาด ถึงขีดจำกัดการส่งข้อความในเดือนนี้")
        print(f"เกิดข้อผิดพลาด: {str(e)}")
    except LineBotApiError as e:
        print(f"เกิดข้อผิดพลาดในการส่งข้อความผ่าน Line: {str(e)}")
        # แจ้งเตือนเมื่อไม่สามารถส่งข้อความผ่าน Line ได้
        if e.status_code == 429:  # กรณีที่จำนวนการส่งข้อความเกินลิมิต
            print("ถึงขีดจำกัดการส่งข้อความในเดือนนี้")
        else:
            print(f"ข้อผิดพลาดที่ไม่รู้จัก: {str(e)}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดทั่วไป: {str(e)}")

    return redirect('dashboard:orders_all')



# ส่งการแจ้งเตือนไปยังผู้จัดการคลัง
def notify_admin_out_of_stock(product_id, user):
    try:
        product = get_object_or_404(Product, id=product_id)
        notification = OutOfStockNotification.objects.filter(product=product, user=user).latest('date_created')

        # ดึง admin และ manager ที่มีบัญชี LINE เชื่อมโยง
        admin_user_ids = UserLine.objects.filter(user__is_warehouse_manager=True).values_list('userId', flat=True)
        admin_user_ids = set(admin_user_ids)  # ใช้ set() เพื่อลดความซ้ำซ้อน
        admin_user_ids.update(
            UserLine.objects.filter(user__is_admin=True).values_list('userId', flat=True)
        )

        # ตรวจสอบว่ามีหมายเหตุหรือไม่
        note_text = f"\n📝 หมายเหตุ: {notification.note}" if notification.note else ""

        # สร้างข้อความแจ้งเตือน
        message = (
            f"🔴 แจ้งเตือนวัสดุหมด! 🔴\n"
            f"📌 {product.product_name} หมดสต๊อกแล้ว\n"
            f"📋 แจ้งโดย: {user.first_name}\n"
            f"📅 โปรดดำเนินการเติมสต๊อกโดยเร็ว{note_text}"
        )

        # ส่งข้อความไปยังแอดมินทุกคน
        for admin_user_id in admin_user_ids:
            try:
                line_bot_api.push_message(admin_user_id, TextSendMessage(text=message))
                print(f"📩 ส่งการแจ้งเตือนวัสดุหมดไปยัง {admin_user_id} สำเร็จ")
            except Exception as e:
                print(f"❌ ไม่สามารถส่งข้อความถึง {admin_user_id}: {str(e)}")

    except Product.DoesNotExist:
        print(f"❌ ไม่พบวัสดุ ID {product_id}")
    except OutOfStockNotification.DoesNotExist:
        print(f"❌ ไม่พบการแจ้งเตือนสำหรับวัสดุ ID {product_id} โดย {user.first_name}")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {str(e)}")




# ส่งการแจ้งเตือนไปยัง Line ผู้ช้งาน เมื่อมีการรับทราบแจ้งเตือน
def send_acknowledge_notification(notification):
    """ ส่งการแจ้งเตือนไปยัง Line เมื่อมีการรับทราบแจ้งเตือน พร้อมโน๊ตจากผู้จัดการคลัง """
    try:
        user_line = get_object_or_404(UserLine, user=notification.user)

        # ตรวจสอบว่ามีโน๊ตจากผู้จัดการคลังหรือไม่
        note_text = f"\n📝 โน๊ตจากผู้จัดการคลัง: {notification.acknowledged_note}" if notification.acknowledged_note else ""

        # สร้างข้อความแจ้งเตือน
        message = (
            f"📌 ผลการแจ้งเตือนวัสดุ: '{notification.product.product_name}' ได้รับการรับทราบแล้ว ✅{note_text}"
        )

        # ส่งข้อความแจ้งเตือนไปยังผู้ใช้
        line_bot_api.push_message(user_line.userId, TextSendMessage(text=message))
        print("📩 ส่งแจ้งเตือนรับทราบสำเร็จ")

    except LineBotApiError as e:
        print(f"❌ เกิดข้อผิดพลาดในการส่งแจ้งเตือนรับทราบ: {str(e)}")
    except Exception as e:
        print(f"❌ ข้อผิดพลาดทั่วไป: {str(e)}")


# ส่งการแจ้งเตือนไปยัง Line ผู้ใช้งาน เมื่อมีการเติมสต๊อก
def send_restock_notification(notification):
    """ ส่งการแจ้งเตือนไปยัง Line เมื่อมีการเติมสต๊อก """
    try:
        user_line = get_object_or_404(UserLine, user=notification.user)

        # ตรวจสอบว่ามีโน๊ตจากผู้จัดการคลังหรือไม่
        note_text = f"\n📝 โน๊ตจากผู้จัดการคลัง: {notification.acknowledged_note}" if notification.acknowledged_note else ""

        message = f"📦 วัสดุ '{notification.product.product_name}' ได้ถูกเติมสต๊อกเรียบร้อยแล้ว 🎉{note_text}"

        line_bot_api.push_message(user_line.userId, TextSendMessage(text=message))
        print("ส่งแจ้งเตือนเติมสต๊อกสำเร็จ")
    except LineBotApiError as e:
        print(f"เกิดข้อผิดพลาดในการส่งแจ้งเตือนเติมสต๊อก: {str(e)}")
    except Exception as e:
        print(f"ข้อผิดพลาดทั่วไป: {str(e)}")




# Line_assets
line_bot_api_asset = LineBotApi("73ckpzhX0833x8i4m/jDhe2lYuGwaTijoooW7dEHndJbl7KUL/6fv4wfa+KXPf3IgSG+8gJ9t8yg2rrCgaAzlg8BtHAiUFVta5BlOGpUz3yuNhaab2KioEspYgX4j5UuapN7WFYGtRfcJqq5SeqzbAdB04t89/1O/w1cDnyilFU=")

# ผูกบัญชี
@csrf_exempt
def linebot(request):
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)

    try:
        body = request.body.decode('utf-8')
        body_json = json.loads(body)
        events = body_json.get('events', [])
    except Exception as e:
        print(f"Error parsing body: {e}")
        return HttpResponse(status=400)

    for event in events:
        userId = event.get('source', {}).get('userId')
        text = event.get('message', {}).get('text', '')

        if not userId:
            continue  # ถ้าไม่มี userId ก็ข้ามไป

        # ตรวจสอบว่ามีการพิมพ์ "ผูกบัญชี"
        if text.startswith('ผูกบัญชี'):
            parts = text.split()

            if len(parts) != 2:
                # แจ้งเตือนถ้าพิมพ์ไม่ถูกต้อง
                line_bot_api_asset.push_message(
                    userId,
                    TextSendMessage(text='⚠ รูปแบบไม่ถูกต้อง\nกรุณาพิมพ์: ผูกบัญชี [Username]')
                )
                continue

            username = parts[1]
            user = MyUser.objects.filter(username=username).first()

            if not user:
                # Username ไม่ถูกต้อง
                line_bot_api_asset.push_message(
                    userId,
                    TextSendMessage(text='❌ ไม่พบบัญชีผู้ใช้\nกรุณาตรวจสอบ Username อีกครั้ง')
                )
                continue

            # ตรวจสอบว่ามีการผูกบัญชีไว้แล้วหรือยัง
            line = UserLine_Asset.objects.filter(user=user).first()

            if not line:
                # ยังไม่มี -> สร้างใหม่
                UserLine_Asset.objects.create(user=user, userId=userId)
                line_bot_api_asset.push_message(
                    userId,
                    TextSendMessage(text=f'✅ ผูกบัญชีสำเร็จ\nสวัสดี {user.get_full_name() or user.username}')
                )
            else:
                # มีแล้ว -> อัปเดต userId
                line.userId = userId
                line.save()
                line_bot_api_asset.push_message(
                    userId,
                    TextSendMessage(text=f'🔄 อัปเดตการผูกบัญชีเรียบร้อย\nสวัสดี {user.get_full_name() or user.username}')
                )

        else:
            # ถ้า user ยังไม่ได้ผูกบัญชี
            linked = UserLine_Asset.objects.filter(userId=userId).first()
            if not linked:
                line_bot_api_asset.push_message(
                    userId,
                    TextSendMessage(text='⚠ กรุณาผูกบัญชีก่อนใช้งาน\nพิมพ์: ผูกบัญชี [Username]')
                )

    return HttpResponse(status=200)



# mapping วันอังกฤษ → วันไทย
DAY_MAP = {
    "Monday": "วันจันทร์",
    "Tuesday": "วันอังคาร",
    "Wednesday": "วันพุธ",
    "Thursday": "วันพฤหัสบดี",
    "Friday": "วันศุกร์",
    "Saturday": "วันเสาร์",
    "Sunday": "วันอาทิตย์",
}
# ส่งแจ้งเตือนไปยังแอดมินเมื่อมีผู้ยืม
def notify_admin_assetloan(request, order_id):
    try:
        order = OrderAssetLoan.objects.get(id=order_id)
    except OrderAssetLoan.DoesNotExist:
        messages.error(request, "ไม่พบออเดอร์การยืมครุภัณฑ์")
        return

    # ดึงผู้ใช้งานที่เป็น manager หรือ admin
    users_to_notify = MyUser.objects.filter(is_warehouse_manager=True) | MyUser.objects.filter(is_admin=True)

    # หา Line User IDs
    admin_user_ids = []
    for user in users_to_notify:
        try:
            user_line = UserLine_Asset.objects.get(user=user)
            admin_user_ids.append(user_line.userId)
        except UserLine_Asset.DoesNotExist:
            print(f"ไม่มี Line ID สำหรับผู้ใช้ {user.username}")

    if not admin_user_ids:
        messages.warning(request, "ไม่พบ Line ID สำหรับผู้ดูแลระบบ")
        return

    # แปลงเวลาให้เป็น Bangkok timezone
    bangkok_tz = pytz.timezone('Asia/Bangkok')
    if timezone.is_naive(order.date_due):
        date_due_local = bangkok_tz.localize(order.date_due)
    else:
        date_due_local = order.date_due.astimezone(bangkok_tz)

    # บังคับ locale เป็นอังกฤษเพื่อให้ %A คืนชื่อวันภาษาอังกฤษ
    try:
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
    except locale.Error:
        pass  # ถ้าเซิร์ฟเวอร์ไม่มี locale en_US ก็ปล่อยไป

    # แปลงวันเป็นไทย
    weekday_en = date_due_local.strftime('%A')
    weekday_th = DAY_MAP.get(weekday_en, 'ไม่ระบุ')

    # สร้างสตริงเวลาแบบ 24 ชม. พร้อมวันไทย
    due_str = date_due_local.strftime('%d/%m/%Y %H:%M')
    due_str = f"{weekday_th} ที่ {due_str} น."

    # ดึงรายการครุภัณฑ์
    items = order.items.select_related("asset").all()
    items_list = "\n".join([
        f"- {item.asset.item_name} ({item.asset.asset_code})"
        for item in items
    ])

    # สร้างข้อความ
    message = (
        f"📑 คำขอยืมครุภัณฑ์ใหม่\n"
        f"ผู้ยืม: {order.user.get_full_name()}\n"
        f"เลขที่ออเดอร์: {order.id}\n"
        f"กำหนดคืน: {due_str}\n\n"
        f"รายการที่ยืม:\n{items_list}"
    )

    # ส่งข้อความ LINE ทีละคน + debug
    try:
        for uid in admin_user_ids:
            line_bot_api_asset.push_message(uid, TextSendMessage(text=message))
        print("✅ ส่งแจ้งเตือน LINE เรียบร้อย:", admin_user_ids)
    except Exception as e:
        import traceback
        print("❌ LINE API Error:", e)
        print(traceback.format_exc())
        messages.warning(request, "ไม่สามารถส่งข้อความแจ้งเตือนผ่าน LINE ได้")



# ------------------------------
# ฟังก์ชันส่งแจ้งเตือนผู้ยืม
# ------------------------------
def notify_borrower(loan, action_type="approved"):
    """
    ส่งข้อความแจ้งเตือนผู้ยืม
    action_type: 'approved', 'rejected', 'returned'
    """
    try:
        user_line = UserLine_Asset.objects.get(user=loan.user)
        user_id = user_line.userId
    except UserLine_Asset.DoesNotExist:
        print(f"❌ ไม่มี Line ID ของผู้ยืม {loan.user.username}")
        return

    # ดึงรายการครุภัณฑ์
    items = loan.items.select_related("asset").all()
    items_list = "\n".join([
        f"- {item.asset.item_name} ({item.asset.asset_code})"
        for item in items
    ])

    # แปลงเวลาให้เป็น Bangkok timezone
    bangkok_tz = pytz.timezone('Asia/Bangkok')
    if timezone.is_naive(loan.date_due):
        date_due_local = bangkok_tz.localize(loan.date_due)
    else:
        date_due_local = loan.date_due.astimezone(bangkok_tz)

    # สร้างสตริงเวลาแบบ 24 ชม.
    due_str = date_due_local.strftime('%d/%m/%Y %H:%M')

    # ข้อความ
    if action_type == "approved":
        text = (
            f"✅ คำขอยืมของคุณถูกอนุมัติแล้ว\n"
            f"เลขที่ออเดอร์: {loan.id}\n\n"
            f"รายการที่ยืม:\n{items_list}\n\n"
            f"⚠️ กรุณาส่งคืนครุภัณฑ์ภายในวันที่ {due_str} น."
        )
    elif action_type == "rejected":
        text = f"❌ คำขอยืมของคุณถูกปฏิเสธ\nเลขที่ออเดอร์: {loan.id}\nเหตุผล/{loan.note or 'ไม่มีระบุ'}"
    elif action_type == "returned":
        text = (f"📦 การคืนครุภัณฑ์ของคุณได้รับการอนุมัติแล้ว\nเลขที่ออเดอร์: {loan.id}\n\n"
                f"รายการที่ยืม:\n{items_list}\n\n"
        )
    else:
        text = f"📌 แจ้งเตือนคำขอของคุณ\nเลขที่ออเดอร์: {loan.id}"

    # ส่งข้อความ
    try:
        line_bot_api_asset.push_message(user_id, TextSendMessage(text=text))
        print(f"✅ ส่ง LINE ไปยังผู้ยืม: {loan.user.username}")
    except Exception as e:
        import traceback
        print(f"❌ LINE API Error: {e}")
        print(traceback.format_exc())


# ----------------------------------------------------
# ฟังก์ชันใหม่: ส่งแจ้งเตือนเจ้าหน้าที่เมื่อมีการบันทึกการคืน
# ----------------------------------------------------
def notify_admin_on_return(loan):
    """
    ส่งข้อความแจ้งเตือนผู้ดูแลระบบเมื่อมีการบันทึกการคืนครุภัณฑ์
    """
    try:
        # ดึงผู้ใช้งานที่เป็น manager หรือ admin
        users_to_notify = MyUser.objects.filter(is_warehouse_manager=True) | MyUser.objects.filter(is_admin=True)

        # หา Line User IDs
        admin_user_ids = []
        for user in users_to_notify:
            try:
                user_line = UserLine_Asset.objects.get(user=user)
                admin_user_ids.append(user_line.userId)
            except UserLine_Asset.DoesNotExist:
                print(f"ไม่มี Line ID สำหรับผู้ใช้ {user.username}")

        if not admin_user_ids:
            print("ไม่พบ Line ID สำหรับผู้ดูแลระบบ")
            return

        # ดึงรายการครุภัณฑ์
        items = loan.items.select_related("asset").all()
        items_list = "\n".join([
            f"- {item.asset.item_name} ({item.asset.asset_code})"
            for item in items
        ])

        # สร้างข้อความ
        message = (
            f"📦 คำขอคืนครุภัณฑ์ใหม่\n"
            f"ผู้ขอคืน: {loan.user.get_full_name()}\n"
            f"เลขที่ออเดอร์: {loan.id}\n\n"
            f"รายการที่คืน:\n{items_list}\n\n"
            f"💡 กรุณาตรวจสอบและอนุมัติการคืนในระบบ"
        )

        # ส่งข้อความ LINE ทีละคน
        for uid in admin_user_ids:
            line_bot_api_asset.push_message(uid, TextSendMessage(text=message))
        print("✅ ส่งแจ้งเตือน LINE ไปยังผู้ดูแลระบบเรียบร้อย")

    except Exception as e:
        import traceback
        print("❌ LINE API Error:", e)
        print(traceback.format_exc())



# mapping วันอังกฤษ → วันไทย
DAY_MAP = {
    "Monday": "วันจันทร์",
    "Tuesday": "วันอังคาร",
    "Wednesday": "วันพุธ",
    "Thursday": "วันพฤหัสบดี",
    "Friday": "วันศุกร์",
    "Saturday": "วันเสาร์",
    "Sunday": "วันอาทิตย์",
}

def notify_admin_on_auto_loan(loan):
    """
    ส่งข้อความแจ้งเตือนผู้ดูแลระบบเมื่อมีการสร้างออเดอร์การยืมอัตโนมัติ
    """
    try:
        users_to_notify = MyUser.objects.filter(is_warehouse_manager=True) | MyUser.objects.filter(is_admin=True)
        admin_user_ids = []
        for user in users_to_notify:
            try:
                user_line = UserLine_Asset.objects.get(user=user)
                admin_user_ids.append(user_line.userId)
            except UserLine_Asset.DoesNotExist:
                continue
        
        if not admin_user_ids:
            return

        # แปลงเวลาให้เป็น Bangkok timezone
        bangkok_tz = pytz.timezone('Asia/Bangkok')
        if timezone.is_naive(loan.date_due):
            date_due_local = bangkok_tz.localize(loan.date_due)
        else:
            date_due_local = loan.date_due.astimezone(bangkok_tz)

        # บังคับ locale เป็นอังกฤษเพื่อให้ %A คืนชื่อวันภาษาอังกฤษ
        try:
            locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        except locale.Error:
            pass

        # แปลงวันเป็นไทย
        weekday_en = date_due_local.strftime('%A')
        weekday_th = DAY_MAP.get(weekday_en, 'ไม่ระบุ')

        # สร้างสตริงเวลาแบบ 24 ชม. พร้อมวันไทย
        due_str = date_due_local.strftime('%d/%m/%Y %H:%M')
        due_str = f"{weekday_th} ที่ {due_str} น."

        items = loan.items.select_related("asset").all()
        items_list = "\n".join([f"- {item.asset.item_name} ({item.asset.asset_code})" for item in items])
        
        message = (
            f"🔔 มีคำขอยืมครุภัณฑ์อัตโนมัติ\n"
            f"ผู้ยืม: {loan.user.get_full_name()}\n"
            f"เลขที่ออเดอร์: {loan.id}\n"
            f"ประเภท: การยืมอัตโนมัติจากการจอง\n"
            f"กำหนดคืน: {due_str}\n\n"
            f"รายการที่ยืม:\n{items_list}\n"
            f"กรุณาตรวจสอบและอนุมัติ"
        )
        
        for uid in admin_user_ids:
            line_bot_api_asset.push_message(uid, TextSendMessage(text=message))
        print("✅ ส่งแจ้งเตือน LINE ไปยังผู้ดูแลระบบ (ยืมอัตโนมัติ) เรียบร้อยแล้ว")
    except Exception as e:
        print(f"❌ LINE API Error (notify_admin_on_auto_loan): {e}")
        print(traceback.format_exc())