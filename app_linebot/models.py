from django.db import models

from accounts.models import MyUser

# Create your models here.
class UserLine(models.Model):
    user = models.ForeignKey(MyUser, verbose_name='IDผู้ใช้งาน', on_delete=models.CASCADE)
    userId = models.CharField(max_length=500)

    def __str__(self):
        return f"{self.user.username}  : {self.userId} : {self.user.first_name}"
    

class UserLine_Asset(models.Model):
    user = models.ForeignKey(MyUser, verbose_name='IDผู้ใช้งาน', on_delete=models.CASCADE)
    userId = models.CharField(max_length=500)

    def __str__(self):
        return f"{self.user.username}  : {self.userId} : {self.user.first_name}"
    
    # **เพิ่มเมธอดนี้เพื่อเรียกใช้งานได้ง่ายขึ้น**
    # @classmethod
    # def is_user_linked(cls, user):
    #     """ตรวจสอบว่าผู้ใช้คนนี้มี UserLine_Asset ผูกบัญชีอยู่แล้วหรือไม่"""
    #     return cls.objects.filter(user=user).exists()