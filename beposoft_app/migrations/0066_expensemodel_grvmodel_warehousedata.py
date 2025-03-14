# Generated by Django 5.1.3 on 2024-11-27 03:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0065_company_alter_order_company'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpenseModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purpose_of_payment', models.TextField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('expense_date', models.DateField()),
                ('transaction_id', models.IntegerField()),
                ('description', models.TextField()),
                ('added_by', models.CharField(max_length=30, null=True)),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='beposoft_app.bank')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='beposoft_app.company')),
                ('payed_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='beposoft_app.user')),
            ],
        ),
        migrations.CreateModel(
            name='GRVModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product', models.CharField(max_length=100)),
                ('returnreason', models.CharField(max_length=200)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quantity', models.IntegerField()),
                ('remark', models.CharField(choices=[('return', 'Return'), ('refund', 'Refund')], max_length=20, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=30, null=True)),
                ('date', models.DateField(null=True)),
                ('time', models.TimeField(null=True)),
                ('note', models.TextField(null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='beposoft_app.order')),
            ],
        ),
        migrations.CreateModel(
            name='Warehousedata',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('box', models.CharField(max_length=100)),
                ('weight', models.CharField(max_length=30)),
                ('length', models.CharField(max_length=30)),
                ('breadth', models.CharField(max_length=30)),
                ('height', models.CharField(max_length=30, null=True)),
                ('image', models.ImageField(null=True, upload_to='images/')),
                ('parcel_service', models.CharField(max_length=30, null=True)),
                ('tracking_id', models.IntegerField(null=True)),
                ('shipping_charge', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('status', models.CharField(max_length=30, null=True)),
                ('shipped_date', models.DateField()),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='warehouse_orders', to='beposoft_app.order')),
                ('packed_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='beposoft_app.user')),
            ],
        ),
    ]
