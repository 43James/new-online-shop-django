# Generated by Django 3.2 on 2024-07-17 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0025_alter_product_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='monthlystockrecord',
            name='total_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='ราคารวม'),
        ),
    ]
