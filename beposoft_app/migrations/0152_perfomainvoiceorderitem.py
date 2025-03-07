# Generated by Django 5.1.3 on 2025-03-07 06:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0151_perfomainvoiceorder'),
    ]

    operations = [
        migrations.CreateModel(
            name='PerfomaInvoiceOrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=100, null=True)),
                ('rate', models.IntegerField()),
                ('tax', models.PositiveIntegerField()),
                ('discount', models.IntegerField(default=0, null=True)),
                ('quantity', models.PositiveIntegerField()),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='perfoma_items', to='beposoft_app.perfomainvoiceorder')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='beposoft_app.products')),
            ],
        ),
    ]
