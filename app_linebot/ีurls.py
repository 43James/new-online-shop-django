from django.urls import path

from . import views

urlpatterns = [
    #lineBot
    path('linebot',views.linebot, name='linebot'),

]