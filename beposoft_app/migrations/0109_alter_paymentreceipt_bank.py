# Generated by Django 5.1.3 on 2025-01-24 09:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0108_bank_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentreceipt',
            name='bank',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='beposoft_app.bank'),
        ),
    ]
