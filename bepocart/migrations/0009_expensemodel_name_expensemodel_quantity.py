# Generated by Django 5.1.3 on 2025-03-04 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bepocart', '0008_loan_enddate_loan_startdate'),
    ]

    operations = [
        migrations.AddField(
            model_name='expensemodel',
            name='name',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='expensemodel',
            name='quantity',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
