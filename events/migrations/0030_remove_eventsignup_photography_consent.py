# Generated by Django 2.2 on 2019-05-02 14:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0029_ticket_comment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventsignup',
            name='photography_consent',
        ),
    ]
