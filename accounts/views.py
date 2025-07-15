from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
import pandas as pd
from app_linebot.models import UserLine
from cart.utils.cart import Cart
from dashboard.views import is_manager
from django.db.models import Q
from orders.models import Order
from django.contrib.auth import logout as auth_logout

from shop.views import count_unconfirmed_orders
from .forms import EditProfileForm, ProfileImageForm, RegistrationForm, ProfileForm, UserLoginForm, ManagerLoginForm, UserProfileForm, UserEditForm, ExtendedProfileForm
from accounts.models import MyUser, Profile, WorkGroup
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.files.base import ContentFile
import base64

from django.core.exceptions import PermissionDenied

def is_manager(user):
    if not user.is_manager:
        raise PermissionDenied
    return True

def is_executive(user):
    if not user.is_executive:
        raise PermissionDenied
    return True

def is_admin(user):
    if not user.is_admin:
        raise PermissionDenied
    return True

def is_authorized(user):
    # ถ้าผู้ใช้เป็น is_manager, is_executive หรือ is_admin อย่างใดอย่างหนึ่ง
    if user.is_manager or user.is_executive or user.is_admin:
        return True
    raise PermissionDenied

def is_authorized_admin(user):
    if is_admin(user):
        return True
    raise PermissionDenied


@login_required
def change_password(request):
    count_unconfirmed = count_unconfirmed_orders(request.user)
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # สำคัญต่อการอัปเดตเซสชันเพื่อป้องกันไม่ให้ผู้ใช้ถูกล็อกเอาท์
            messages.success(request, 'รหัสผ่านของคุณได้รับการอัปเดตเรียบร้อยแล้ว!')

            # ปริ้นข้อมูลของผู้ใช้เมื่อเปลี่ยนรหัสผ่าน
            print(f"ผู้ใช้ {request.user.first_name} ได้เปลี่ยนรหัสผ่านเรียบร้อยแล้ว")

            return redirect('shop:home_page')
        else:
            messages.error(request, 'กรุณาแก้ไขข้อผิดพลาดด้านล่าง.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', 
                  {'form': form,
                    'count_unconfirmed_orders': count_unconfirmed,})


@user_passes_test(is_authorized_admin)
@login_required
def user_register(request):
    if request.method == 'POST':
        user_form = RegistrationForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            messages.success(request, 'เพิ่มสมาชิกสำเร็จ')
            return redirect('accounts:manage_user')
        else:
            messages.error(request, 'เพิ่มสมาชิกไม่สำเร็จ')
            
    else:
        user_form = RegistrationForm()
        profile_form = ProfileForm()

    return render(request, 'register.html', {
        'title' : 'เพิ่มสมาชิก',
        'user_form': user_form, 
        'profile_form': profile_form
        })



def manager_login(request):
    if request.method == 'POST':
        form = ManagerLoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = authenticate(
                request, username=data['username'], password=data['password']
            )
            if user is not None:
                if user.is_executive:
                    login(request, user)
                    return redirect('dashboard:orders')
                
                elif user.is_manager:
                    login(request, user)
                    return redirect('dashboard:orders')
                
                elif user.is_admin:
                    login(request, user)
                    return redirect('accounts:manage_user')
                
                else:
                    messages.error(
                        request, 'คุณไม่มีสิทธิ์เข้าถึง', 'danger'
                    )
            else:
                messages.error(
                    request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'danger'
                )
                return redirect('accounts:manager_login')
    else:
        form = ManagerLoginForm()
    context = { 'title':'LogIn','form': form}
    return render(request, 'manager_login.html', context)



# def user_login(request):
#     if request.method == 'POST':
#         form = UserLoginForm(request.POST)
#         if form.is_valid():
#             data = form.cleaned_data
#             user = authenticate(
#                 request, username=data['username'], password=data['password']
#             )
#             if user is not None:
#                 if user.is_general:
#                     login(request, user)
#                     return redirect('shop:home_page')
                
#                 elif user.is_manager:
#                     login(request, user)
#                     return redirect('shop:home_page')
                
#                 elif user.is_admin:
#                     login(request, user)
#                     return redirect('shop:home_page')
                
#                 elif user.is_executive:
#                     login(request, user)
#                     return redirect('dashboard:dashboard_home')
                
#                 else:
#                     messages.error(
#                         request, 'คุณไม่มีสิทธิ์เข้าถึง', 'danger'
#                     )
#             else:
#                 messages.error(
#                     request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'danger'
#                 )
#                 return redirect('accounts:user_login')
#     else:
#         form = UserLoginForm()
#     context = {
#         'title':'Login', 'form': form}
#     return render(request, 'login.html', context)

def user_login(request):
    if request.user.is_authenticated:
        if request.user.is_general or request.user.is_manager or request.user.is_admin:
            return redirect('shop:home_page')
        elif request.user.is_executive:
            return redirect('dashboard:dashboard_home')
        else:
            messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึง', 'danger')
            return redirect('shop:home_page')  # หรือไปยังหน้าที่เหมาะสม

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = authenticate(request, username=data['username'], password=data['password'])
            if user is not None:
                login(request, user)
                if user.is_general or user.is_manager or user.is_admin:
                    return redirect('shop:home_page')
                elif user.is_executive:
                    return redirect('dashboard:dashboard_home')
            else:
                messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'danger')
    else:
        form = UserLoginForm()

    context = {'title': 'Login', 'form': form}
    return render(request, 'login.html', context)


# ใหม่8
@login_required
def user_logout(request):
    # เก็บ session ไว้ก่อนที่จะ logout
    cart = Cart(request)
    cart.save()
    
    # ออกจากระบบ
    logout(request)
    
    # คืน session หลังจากที่ logout เสร็จสิ้น
    cart.logout()
    return redirect('accounts:user_login')

# def manager_logout(request):
#     # เก็บ session ไว้ก่อนที่จะ logout
#     cart = Cart(request)
#     cart.save()
    
#     # ออกจากระบบ
#     logout(request)
    
#     # คืน session หลังจากที่ logout เสร็จสิ้น
#     cart.logout()
#     return redirect('accounts:manager_login')


@user_passes_test(is_admin)
@login_required
def manager_edit_profile(request, user_id):
    profile = get_object_or_404(Profile, user__id=user_id)
    
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'บันทึกข้อมูลสำเร็จ')
            return redirect('accounts:manage_user')
        
    else:
        form = EditProfileForm(instance=profile)
    
    context = {
        'title':'แก้ไขข้อมูลผู้ใช้งาน',
        'form': form, 
        'profile': profile,
            }
    
    return render(request, 'manager_edit_profil.html', context)


@login_required
def edit_profile (request):
    user = request.user
    if request.method == "POST":
        form = UserProfileForm(request.POST,  instance=user )
        is_new_profile = False
        
        try:
            #update
            extended_form = ExtendedProfileForm(request.POST, request.FILES, instance=user.profile)
        except:
            #create
            extended_form = ExtendedProfileForm(request.POST, request.FILES)
            is_new_profile = True

        if form.is_valid() and extended_form.is_valid():
            form. save()

            if is_new_profile:
                #create
                profile = extended_form.save(commit=False)
                profile.user = user
                profile.save()
                messages.success(request, 'บันทึกข้อมูลสำเร็จ')
            else:
                #update
                extended_form.save()
                messages.success(request, 'บันทึกข้อมูลสำเร็จ')
            return redirect('accounts:user_profile_detail', username=request.user.username)

    else:
        form = UserProfileForm(instance=user)
        try:
            extended_form = ExtendedProfileForm(instance=user.profile)
        except:
            extended_form = ExtendedProfileForm(request.POST, request.FILES)
    count_unconfirmed = count_unconfirmed_orders(request.user)

    context = {
        'title':'แก้ไขโปรไฟล์',
        "form": form,
        "extended_form": extended_form,
        'pending_orders_count': count_pending_orders(),
        'count_unconfirmed_orders': count_unconfirmed,
    }
    return render(request, 'edit_profile.html', context)



@user_passes_test(is_authorized)
@login_required
def edit_profile_manager (request):
    user = request.user
    if request.method == "POST":
        form = UserProfileForm(request.POST,  instance=user )
        is_new_profile = False
        
        try:
            #update
            extended_form = ExtendedProfileForm(request.POST, request.FILES, instance=user.profile)
        except:
            #create
            extended_form = ExtendedProfileForm(request.POST, request.FILES)
            is_new_profile = True

        if form.is_valid() and extended_form.is_valid():
            form. save()

            if is_new_profile:
                #create
                profile = extended_form.save(commit=False)
                profile.user = user
                profile.save()
                messages.success(request, 'บันทึกข้อมูลสำเร็จ')
            else:
                #update
                extended_form.save()
                messages.success(request, 'บันทึกข้อมูลสำเร็จ')
            return redirect('accounts:manager_profile_detail', username=request.user.username)

    else:
        form = UserProfileForm(instance=user)
        try:
            extended_form = ExtendedProfileForm(instance=user.profile)
        except:
            extended_form = ExtendedProfileForm(request.POST, request.FILES)

    context = {
        'title':'แก้ไขโปรไฟล์',
        "form": form,
        "extended_form": extended_form,
        'pending_orders_count': count_pending_orders(),
    }
    return render(request, 'edit_profile_manager.html', context)



@login_required
def user_profile_detail(request, username):
    count_unconfirmed = count_unconfirmed_orders(request.user)
    try:
        obj = 1
        user = MyUser.objects.get(username = username)
        profile = Profile.objects.get(user_id=user.id)

    except:
        obj = 2
        profile = 'คุณยังไม่ได้เพิ่มข้อมูลโปรไฟล์'
        
    context = {
        'title' : 'โปรไฟล์',
        'user': user, 
        'profile': profile,
        'obj': obj,
        'pending_orders_count': count_pending_orders(),
        'count_unconfirmed_orders': count_unconfirmed,
    }
    return render(request, 'user_profile.html', context)




@login_required
def delete_profile_picture(request):
    profile = request.user.profile
    if profile.img:
        profile.img.delete()
        messages.success(request, 'รูปโปรไฟล์ถูกลบเรียบร้อยแล้ว')
    else:
        messages.error(request, 'ไม่มีรูปโปรไฟล์ให้ลบ')
    return redirect('accounts:user_profile_detail', username=request.user.username)




@login_required
def upload_profile_picture(request):
    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES)
        if form.is_valid():
            profile = request.user.profile
            cropped_image_data = request.POST.get('cropped_image')
            if cropped_image_data:
                # Decode the image from base64
                format, imgstr = cropped_image_data.split(';base64,') 
                ext = format.split('/')[-1] 
                img_data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
                profile.img.save(f'{request.user.username}.{ext}', img_data, save=False)
            else:
                profile.img = form.cleaned_data['img']
            profile.save()
            messages.success(request, 'รูปโปรไฟล์ถูกอัพโหลดเรียบร้อยแล้ว')
            return redirect('accounts:user_profile_detail', username=request.user.username)
    else:
        form = ProfileImageForm()
    count_unconfirmed = count_unconfirmed_orders(request.user)
    context = {
        'title' : 'อัพโหลดรูปโปรไฟล์',
        'form': form,
        'pending_orders_count': count_pending_orders(),
        'count_unconfirmed_orders': count_unconfirmed,
        
    }
    return render(request, 'upload_profile_picture.html', context)




@login_required
def upload_profile_picture_manager(request):
    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES)
        if form.is_valid():
            profile = request.user.profile
            cropped_image_data = request.POST.get('cropped_image')
            if cropped_image_data:
                # Decode the image from base64
                format, imgstr = cropped_image_data.split(';base64,') 
                ext = format.split('/')[-1] 
                img_data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
                profile.img.save(f'{request.user.username}.{ext}', img_data, save=False)
            else:
                profile.img = form.cleaned_data['img']
            profile.save()
            messages.success(request, 'รูปโปรไฟล์ถูกอัพโหลดเรียบร้อยแล้ว')
            return redirect('accounts:manager_profile_detail', username=request.user.username)
    else:
        form = ProfileImageForm()
    context = {
        'title' : 'อัพโหลดรูปโปรไฟล์',
        'form': form,
        'pending_orders_count': count_pending_orders(),
    }
    return render(request, 'upload_profile_picture_manager.html', context)


@user_passes_test(is_authorized)
@login_required
def manager_profile_detail(request, username):
    try:
        obj = 1
        user = MyUser.objects.get(username = username)
        profile = Profile.objects.get(user_id=user.id)

    except:
        obj = 2
        profile = 'คุณยังไม่ได้เพิ่มข้อมูลโปรไฟล์'
        
    context = {
        'title' : 'โปรไฟล์',
        'user': user, 
        'profile': profile,
        'obj': obj,
        'pending_orders_count': count_pending_orders(),
    }
    return render(request, 'manager_profile.html', context)


@user_passes_test(is_authorized)
# @login_required
# def profile_users(request, username):
        
#     try:
#         obj = 1
#         users = MyUser.objects.get(username = username)
#         profiles = Profile.objects.get(user_id=users.id)

#     except:
#         obj = 2
#         profiles = 'ผู้ใช้งานยังไม่ได้เพิ่มข้อมูลโปรไฟล์'
        
#     context = {
#         'title' : 'ข้อมูลโปรไฟล์ผู้ใช้งาน',
#         'user': users, 
#         'profile': profiles,
#         'obj': obj,
#         'pending_orders_count': count_pending_orders(),
#     }
#     return render(request, 'profile_users.html', context)

@login_required
def profile_users(request, username):
    try:
        obj = 1
        users = MyUser.objects.get(username=username)
        profiles = Profile.objects.get(user_id=users.id)

        # ตรวจสอบการผูกบัญชีไลน์
        line_user_exists = UserLine.objects.filter(user=users).first()

    except MyUser.DoesNotExist:
        obj = 2
        profiles = 'ผู้ใช้งานยังไม่ได้เพิ่มข้อมูลโปรไฟล์'
        line_user_exists = False  # กรณีไม่มีการผูกบัญชี
        
    context = {
        'title': 'ข้อมูลโปรไฟล์ผู้ใช้งาน',
        'user': users, 
        'profile': profiles,
        'obj': obj,
        'pending_orders_count': count_pending_orders(),
        'line_user_exists': line_user_exists,  # ส่งสถานะการผูกบัญชีไลน์
    }
    return render(request, 'profile_users.html', context)


@user_passes_test(is_authorized)
@login_required
def delete_profile_picture_manager(request):
    profile = request.user.profile
    if profile.img:
        profile.img.delete()
        messages.success(request, 'รูปโปรไฟล์ถูกลบเรียบร้อยแล้ว')
    else:
        messages.error(request, 'ไม่มีรูปโปรไฟล์ให้ลบ')
    return redirect('accounts:manager_profile_detail', username=request.user.username)


@user_passes_test(is_admin)
@login_required
def manage_user(request):
    # my = MyUser.objects.all()
    my = MyUser.objects.prefetch_related('userline_set').all()  # โหลด user ทั้งหมดพร้อม UserLine

    userline = UserLine.objects.all()
    
    query = request.GET.get('q')
    if query is not None:
        lookups = Q(username__icontains=query) | Q(first_name__icontains=query)
        my = MyUser.objects.filter(lookups)

    page = request.GET.get('page')
    p = Paginator(my, 15)
    try:
        my = p.page(page)
    except:
        my = p.page(1)

    return render(request, "manage_user.html",{
        "my" : my,
        "userline" : userline,
        'title':'จัดการสมาชิก',
        'pending_orders_count': count_pending_orders(),
    })


@user_passes_test(is_admin)
def import_users_from_excel(request):
     if request.method == 'POST':
        file = request.FILES['file']
        try:
            df = pd.read_excel(file)

            for index, row in df.iterrows():
                password = row['password'] if 'password' in row and pd.notna(row['password']) else 'default_password'
                is_active = row['is_active'] if 'is_active' in row and pd.notna(row['is_active']) else True

                user, created = MyUser.objects.update_or_create(
                    username=row['username'],
                    defaults={
                        'perfix': row['perfix'],
                        'first_name': row['first_name'],
                        'last_name': row['last_name'],
                        'email': row['email'],
                        'is_active': is_active,
                        'is_general': row['is_general'],
                        'is_manager': row['is_manager'],
                        'is_executive': row['is_executive'],
                        'is_admin': row['is_admin'],
                        'password': make_password(password),
                    }
                )

                workgroup, _ = WorkGroup.objects.get_or_create(work_group=row['workgroup'])

                Profile.objects.update_or_create(
                    user=user,
                    defaults={
                        'gender': row['gender'],
                        'workgroup': workgroup,
                        'position': row['position'],
                        'phone': row['phone'],
                        'img': row['img'] if 'img' in row and pd.notna(row['img']) else None,
                    }
                )
            
            messages.success(request, 'นำเข้าข้อมูลผู้ใช้งานสำเร็จ')
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาดในการนำเข้าข้อมูล: {e}')
        
        return redirect('accounts:manage_user')
     

@user_passes_test(is_admin)
def export_users_to_excel(request):
    users = MyUser.objects.all()
    profiles = Profile.objects.filter(user__in=users)

    user_data = []
    for user in users:
        profile = profiles.filter(user=user).first()

        # Convert to timezone unaware datetime
        user_date_created = timezone.localtime(user.date_created).replace(tzinfo=None) if user.date_created else None
        profile_date_created = timezone.localtime(profile.updatedAt).replace(tzinfo=None) if profile and profile.updatedAt else None

        user_data.append({
            'username': user.username,
            'perfix': user.perfix,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'is_active': user.is_active,
            'is_general': user.is_general,
            'is_manager': user.is_manager,
            'is_executive': user.is_executive,
            'is_admin': user.is_admin,
            'date_created': user_date_created,
            'gender': profile.gender if profile else '',
            'workgroup': profile.workgroup.work_group if profile else '',
            'position': profile.position if profile else '',
            'phone': profile.phone if profile else '',
            'img': profile.img.url if profile and profile.img else '',
            'profile_date_created': profile_date_created,
        })

    df = pd.DataFrame(user_data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=users.xlsx'

    # Save to Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Users')

    return response



@user_passes_test(is_admin)
@login_required
def update_user(request, id):
    my = MyUser.objects.get(id=id)
    form = UserEditForm(instance=my)

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=my)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = form.cleaned_data['is_general'] or form.cleaned_data['is_executive'] or form.cleaned_data['is_manager']  or form.cleaned_data['is_admin']
            user.save()

            messages.success(request, 'แก้ไขข้อมูลสำเร็จ')
            return redirect('accounts:manage_user')
        else:
            messages.error(request, 'กรุณากรอกข้อมูลให้ครบถ้วน')

    return render(request, 'update_user.html', {
        'my': my,
        'form': form,
        'title': 'แก้ไขข้อมูลสมาชิก',
        'pending_orders_count': count_pending_orders(),
    })


@user_passes_test(is_admin)
@login_required 
def delete_user(request, id):
    data_input = MyUser.objects
    delete_fil = data_input.filter(id=id).delete()
    data_all = MyUser.objects.all()
    messages.success(request, 'ลบสมาชิกสำเร็จ')
    return redirect('accounts:manage_user')


def count_pending_orders():
    # ดึงข้อมูลออเดอร์ทั้งหมดที่รอการยืนยัน
    pending_orders = Order.objects.filter(status=None)
    return pending_orders.count()
