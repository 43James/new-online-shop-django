# Generated by Django 3.2 on 2024-09-24 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0023_auto_20240906_1100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issuing',
            name='note',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='หมายเหตุ'),
        ),
        migrations.AlterField(
            model_name='order',
            name='other',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='หมายเหตุ'),
        ),
    ]
