# Generated by Django 5.1.7 on 2025-06-13 21:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='service',
            name='duration',
        ),
    ]
