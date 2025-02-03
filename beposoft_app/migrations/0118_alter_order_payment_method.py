# Generated by Django 5.1.3 on 2025-01-30 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0117_alter_order_payment_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('Credit Card', 'Credit Card'), ('Debit Card', 'Debit Card'), ('PayPal', 'PayPal'), ('1 Razorpay', '1 Razorpay'), ('Net Banking', 'Net Banking'), ('Bank Transfer', 'Bank Transfer'), ('Cash on Delivery (COD)', 'Cash on Delivery (COD)')], default='Net Banking', max_length=50),
        ),
    ]
