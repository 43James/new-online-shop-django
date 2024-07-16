# Generated by Django 3.2 on 2024-07-15 02:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0023_remove_product_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receiving',
            name='month',
            field=models.PositiveIntegerField(default=7, editable=False, verbose_name='เดือนที่รับเข้า'),
        ),
        migrations.AlterField(
            model_name='receiving',
            name='year',
            field=models.PositiveIntegerField(default=2024, editable=False, verbose_name='ปีที่รับเข้า'),
        ),
    ]
