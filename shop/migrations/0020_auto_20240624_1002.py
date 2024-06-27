# Generated by Django 3.2 on 2024-06-24 03:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0019_monthlystockrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='receiving',
            name='month',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='เดือนที่รับเข้า'),
        ),
        migrations.AddField(
            model_name='receiving',
            name='year',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='ปีที่รับเข้า'),
        ),
    ]
