# Generated by Django 2.2 on 2019-05-06 09:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0031_auto_20190504_1010'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventsignup',
            name='comment_added_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]