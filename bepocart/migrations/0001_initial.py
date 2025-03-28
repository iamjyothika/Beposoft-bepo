# Generated by Django 5.1.3 on 2025-02-27 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Loan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('principal', models.DecimalField(decimal_places=2, help_text='Total loan amount', max_digits=15)),
                ('annual_interest_rate', models.DecimalField(decimal_places=2, help_text='Annual interest rate in %', max_digits=5)),
                ('tenure_months', models.IntegerField(help_text='Loan duration in months')),
                ('processing_fee', models.DecimalField(blank=True, decimal_places=2, help_text='Optional processing fee', max_digits=10, null=True)),
                ('down_payment', models.DecimalField(blank=True, decimal_places=2, help_text='Initial payment to reduce loan amount', max_digits=15, null=True)),
                ('prepayment_amount', models.DecimalField(blank=True, decimal_places=2, help_text='Extra payment towards principal', max_digits=15, null=True)),
            ],
        ),
    ]
