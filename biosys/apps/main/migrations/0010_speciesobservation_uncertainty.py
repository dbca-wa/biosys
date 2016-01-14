# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_speciesobservation_validation_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='speciesobservation',
            name='uncertainty',
            field=models.CharField(max_length=50, verbose_name='Species uncertainty', blank=True),
        ),
    ]
