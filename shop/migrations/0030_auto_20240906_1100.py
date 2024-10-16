# Generated by Django 3.2 on 2024-09-06 04:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0029_receiving_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receiving',
            name='month',
            field=models.PositiveIntegerField(default=9, editable=False, verbose_name='เดือนที่รับเข้า'),
        ),
        migrations.DeleteModel(
            name='TotalQuantity',
        ),
    ]