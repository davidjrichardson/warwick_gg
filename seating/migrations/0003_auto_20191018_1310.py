# Generated by Django 2.2.6 on 2019-10-18 12:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seating', '0002_remove_seating_table'),
    ]

    operations = [
        migrations.RenameField(
            model_name='seating',
            old_name='seat',
            new_name='seat_id',
        ),
    ]
