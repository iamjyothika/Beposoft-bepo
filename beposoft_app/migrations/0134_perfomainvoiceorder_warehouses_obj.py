# Generated by Django 5.1.3 on 2025-02-20 10:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0133_alter_customers_gst'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfomainvoiceorder',
            name='warehouses_obj',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='beposoft_app.warehouse'),
        ),
    ]
