from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from accounts import views


app_name = 'accounts'

urlpatterns = [
    path('', views.portal_hub, name='portal_hub'),
    path('portal/toggle-favorite/<int:app_id>/', views.toggle_portal_favorite, name='toggle_portal_favorite'),
    path('portal/add/', views.add_portal_app, name='add_portal_app'),
    path('portal/edit/<int:app_id>/', views.edit_portal_app, name='edit_portal_app'),
    path('login/', views.user_login, name='user_login'),
    path('register/', views.user_register, name='user_register'),
    path('login/manager/', views.manager_login, name='manager_login'),
    path('logout/', views.user_logout, name='user_logout'),
    # path('logout/', views.manager_logout, name='manager_logout'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/delete-picture/', views.delete_profile_picture, name='delete_profile_picture'),
    path('profile/delete-picture-manager/', views.delete_profile_picture_manager, name='delete_profile_picture_manager'),
    path('profile/upload-picture/', views.upload_profile_picture, name='upload_profile_picture'),
    path('profile/upload-picture-manager/', views.upload_profile_picture_manager, name='upload_profile_picture_manager'),
    path('profile/edit/manager/', views.edit_profile_manager, name='edit_profile_manager'),
    path('profile/user/<str:username>/', views.user_profile_detail, name='user_profile_detail'),
    path('profile/manager/<str:username>/', views.manager_profile_detail, name='manager_profile_detail'),
    path('profile/<str:username>/', views.profile_users, name='profile_users'),
    path('change_password/', views.change_password, name='change_password'),
    # path('update-product-status/<int:product_id>/', views.update_product_status, name='update_product_status'),
    # urls.py
    path('update-all-products-status/', views.update_all_products_status, name='update_all_products_status'),


    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/auth/password_reset.html',
            success_url=reverse_lazy('accounts:password_reset_done'),
            email_template_name='accounts/other/email_template.html'
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/auth/password_reset_done.html',
        ),
        name='password_reset_done'
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/auth/password_reset_confirm.html',
            success_url=reverse_lazy('accounts:password_reset_complete'),
        ),
        name='password_reset_confirm'
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/auth/password_reset_complete.html',
        ),
        name='password_reset_complete'
    ),
    path('manage/user/', views.manage_user, name='manage_user'),
    path('manager_edit_profile/<int:user_id>/', views.manager_edit_profile, name='manager_edit_profile'),
    path('update/user/<int:id>/', views.update_user, name='update_user'),
    path('delete/user/<int:id>/', views.delete_user, name='delete_user'),
    path('import-users/', views.import_users_from_excel, name='import_users'),
    path('export-users/', views.export_users_to_excel, name='export_users'),

]

