# Generated by Django 5.1.3 on 2025-02-03 05:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0128_alter_customers_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customers',
            name='city',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
