# Generated by Django 3.2 on 2024-07-10 09:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0022_remove_product_unitprice'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='slug',
        ),
    ]
