# Generated by Django 5.1.3 on 2025-02-01 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0126_warehouse_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customers',
            name='phone',
            field=models.CharField(max_length=10, null=True),
        ),
    ]
