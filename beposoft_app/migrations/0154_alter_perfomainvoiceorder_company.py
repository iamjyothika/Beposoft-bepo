# Generated by Django 5.1.3 on 2025-03-07 11:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0153_merge_20250307_1633'),
    ]

    operations = [
        migrations.AlterField(
            model_name='perfomainvoiceorder',
            name='company',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='perfoma_companies', to='beposoft_app.company'),
        ),
    ]
