# Generated by Django 5.1.3 on 2025-01-02 04:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0082_alter_order_company'),
    ]

    operations = [
        migrations.AlterField(
            model_name='beposoftcart',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='beposoft_app.products'),
        ),
    ]
