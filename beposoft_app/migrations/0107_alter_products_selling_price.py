# Generated by Django 5.1.3 on 2025-01-23 04:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0106_alter_products_landing_cost'),
    ]

    operations = [
        migrations.AlterField(
            model_name='products',
            name='selling_price',
            field=models.FloatField(default=0.0, null=True),
        ),
    ]
