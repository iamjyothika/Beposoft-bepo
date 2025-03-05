# Generated by Django 5.1.3 on 2025-02-27 04:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0141_products_purchase_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='products',
            name='approval_status',
            field=models.CharField(choices=[('Approved', 'Approved'), ('Disapproved', 'Disapproved')], default='Disapproved', max_length=100),
        ),
    ]
