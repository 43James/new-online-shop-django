# Generated by Django 3.2 on 2024-08-19 02:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0020_auto_20240717_0932'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issuing',
            name='month',
            field=models.PositiveIntegerField(default=8, editable=False, verbose_name='เดือน'),
        ),
        migrations.AlterField(
            model_name='order',
            name='month',
            field=models.PositiveIntegerField(default=8, editable=False, verbose_name='เดือน'),
        ),
    ]
