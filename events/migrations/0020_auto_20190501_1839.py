# Generated by Django 2.2 on 2019-05-01 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0019_auto_20190501_1650'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventsignup',
            name='comment',
            field=models.TextField(blank=True, default='', max_length=255),
            preserve_default=False,
        ),
    ]
