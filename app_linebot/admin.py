from django.contrib import admin

from app_linebot.models import UserLine, UserLine_Asset

# Register your models here.

admin.site.register(UserLine)
admin.site.register(UserLine_Asset)
