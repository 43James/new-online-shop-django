# Generated by Django 3.2 on 2024-05-23 04:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_alter_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.BooleanField(blank=True, default='', null=True, verbose_name='สถานะ'),
        ),
    ]
