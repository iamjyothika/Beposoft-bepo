# Generated by Django 5.1.3 on 2025-01-31 07:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0118_alter_order_payment_method'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customers',
            name='phone',
            field=models.CharField(max_length=10, null=True, unique=True),
        ),
    ]
