# Generated by Django 3.2 on 2024-04-18 08:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_stock'),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issuing',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Issuing', to='shop.product', verbose_name='สินค้า'),
        ),
    ]
