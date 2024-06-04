from django.urls import path

from .import views

app_name = "app_linebot"

urlpatterns = [
    #lineBot
    path('linebot/',views.linebot, name='linebot'),




]