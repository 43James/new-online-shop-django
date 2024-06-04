# Generated by Django 3.2 on 2024-05-23 09:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0015_alter_receiving_quantity'),
        ('orders', '0010_auto_20240523_1434'),
    ]

    operations = [
        migrations.AddField(
            model_name='issuing',
            name='receiving',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='issuings', to='shop.receiving', verbose_name='รายการรับเข้า'),
            preserve_default=False,
        ),
    ]
