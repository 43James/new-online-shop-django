# Generated by Django 3.2 on 2024-07-16 08:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_auto_20240715_0914'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profile',
            options={'ordering': ['-workgroup'], 'verbose_name': 'ข้อมูลสมาชิก Profile'},
        ),
    ]