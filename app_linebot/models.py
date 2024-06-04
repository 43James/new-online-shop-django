from django.db import models

from accounts.models import MyUser

# Create your models here.
class UserLine(models.Model):
    user = models.ForeignKey(MyUser, verbose_name='IDผู้ใช้งาน', on_delete=models.CASCADE)
    userId = models.CharField(max_length=500)

    def __str__(self):
        return f"{self.user.username}  : {self.userId}"