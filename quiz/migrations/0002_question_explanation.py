# Generated by Django 5.2.3 on 2025-06-30 03:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='explanation',
            field=models.TextField(blank=True, default=''),
        ),
    ]
