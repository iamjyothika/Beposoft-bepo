# Generated by Django 5.1.3 on 2024-12-30 08:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0081_alter_order_company'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='company',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='companies', to='beposoft_app.company'),
        ),
    ]
