from django.urls import path

from .import views

app_name = "app_linebot"

urlpatterns = [
    #lineBot
    path('linebot/',views.linebot, name='linebot'),
    path('linebot-assets/',views.linebot_assets, name='linebot_assets'),
    path('send-receive-confirmation/<int:order_id>/', views.send_receive_confirmation, name='send_receive_confirmation'),




]