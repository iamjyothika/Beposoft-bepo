# Generated by Django 5.1.3 on 2025-03-07 12:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bepocart', '0019_delete_choices'),
    ]

    operations = [
        migrations.CreateModel(
            name='Choices',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True)),
            ],
        ),
    ]
