# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20150617_1016'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='latitude',
            field=models.FloatField(default=-18.0, help_text='Latitude of site origin (e.g. corner, centroid, etc., required)', verbose_name='Latitude'),
        ),
        migrations.AlterField(
            model_name='site',
            name='longitude',
            field=models.FloatField(default=125.0, help_text='Longitude of site origin (e.g. corner, centroid, etc., required)', verbose_name='Longitude'),
        ),
    ]
