# Generated by Django 5.1.3 on 2025-02-20 12:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0134_perfomainvoiceorder_warehouses_obj'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='perfomainvoiceorder',
            name='bank',
        ),
    ]
