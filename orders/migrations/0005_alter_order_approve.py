# Generated by Django 3.2 on 2024-04-30 09:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_alter_order_approve'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='approve',
            field=models.BooleanField(default=False, verbose_name='อนุมัติ'),
        ),
    ]
