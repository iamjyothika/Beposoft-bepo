# Generated by Django 5.1.3 on 2025-03-04 05:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0147_alter_expensemodel_bank_alter_expensemodel_company_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='expensemodel',
            name='loan',
        ),
        migrations.AlterField(
            model_name='expensemodel',
            name='bank',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='banks', to='beposoft_app.bank'),
        ),
        migrations.AlterField(
            model_name='expensemodel',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='company', to='beposoft_app.company'),
        ),
        migrations.AlterField(
            model_name='expensemodel',
            name='payed_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payed_by', to='beposoft_app.user'),
        ),
        migrations.AlterField(
            model_name='expensemodel',
            name='purpose_of_payment',
            field=models.CharField(choices=[('water', 'Water'), ('electricity', 'Electricity'), ('salary', 'Salary'), ('emi', 'EMI'), ('rent', 'Rent'), ('equipments,', 'Equipments'), ('travel', 'Travel'), ('others', 'Others')], max_length=100, null=True),
        ),
    ]
