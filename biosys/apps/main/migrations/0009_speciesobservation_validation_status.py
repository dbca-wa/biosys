# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_auto_20150623_0924'),
    ]

    operations = [
        migrations.AddField(
            model_name='speciesobservation',
            name='validation_status',
            field=models.CharField(default='', choices=[('', ''), ('do not validate', 'do not validate')], max_length=50, blank=True, null=True, verbose_name='Species validation status'),
        ),
    ]
