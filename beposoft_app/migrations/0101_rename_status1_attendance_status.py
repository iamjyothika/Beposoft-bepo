# Generated by Django 5.1.3 on 2025-01-21 11:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('beposoft_app', '0100_rename_status_attendance_status1'),
    ]

    operations = [
        migrations.RenameField(
            model_name='attendance',
            old_name='status1',
            new_name='status',
        ),
    ]
