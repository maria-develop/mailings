# Generated by Django 5.1.2 on 2024-10-12 12:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailings', '0005_alter_mailing_options_alter_mailing_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailingattempt',
            name='mailing',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attempts', related_query_name='attempts', to='mailings.mailing'),
        ),
    ]
