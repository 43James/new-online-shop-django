# Generated by Django 3.2.6 on 2025-01-24 07:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0034_alter_receiving_month'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receiving',
            name='month',
            field=models.PositiveIntegerField(default=1, editable=False, verbose_name='เดือนที่รับเข้า'),
        ),
        migrations.AlterField(
            model_name='receiving',
            name='year',
            field=models.PositiveIntegerField(default=2025, editable=False, verbose_name='ปีที่รับเข้า'),
        ),
    ]
