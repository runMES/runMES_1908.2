# Generated by Django 2.2.1 on 2019-09-10 01:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('runMES', '0002_auto_20190910_0950'),
    ]

    operations = [
        migrations.RenameField(
            model_name='alarmhist',
            old_name='alarm_code',
            new_name='alarm_id',
        ),
    ]
