# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-29 06:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_form_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='form',
            name='dataset',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='main.Dataset'),
            preserve_default=False,
        ),
    ]
