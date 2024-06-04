from django.urls import include, path, reverse_lazy
from django.contrib.auth import views as auth_views

from accounts import views


app_name = 'accounts'

urlpatterns = [
    path('', views.user_login, name='user_login'),
    path('register/', views.user_register, name='user_register'),
    path('login/manager/', views.manager_login, name='manager_login'),
    path('logout/', views.user_logout, name='user_logout'),
    # path('logout/', views.manager_logout, name='manager_logout'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/edit/manager/', views.edit_profile_manager, name='edit_profile_manager'),
    path('profile/user/<str:username>/', views.user_profile_detail, name='user_profile_detail'),
    path('profile/manager/<str:username>/', views.manager_profile_detail, name='manager_profile_detail'),
    path('change_password/', views.change_password, name='change_password'),


    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='password_reset.html',
            success_url=reverse_lazy('accounts:password_reset_done'),
            email_template_name='email_template.html'
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done',
        auth_views.PasswordResetDoneView.as_view(
            template_name='password_reset_done.html',
        ),
        name='password_reset_done'
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html',
            success_url=reverse_lazy('accounts:password_reset_complete'),
        ),
        name='password_reset_confirm'
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='password_reset_complete.html',
        ),
        name='password_reset_complete'
    ),
    path('manage/user/', views.manage_user, name='manage_user'),
    path('update/user/<int:id>/', views.update_user, name='update_user'),
    path('delete/user/<int:id>/', views.delete_user, name='delete_user'),

]

