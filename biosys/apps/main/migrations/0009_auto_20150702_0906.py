# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_auto_20150623_0924'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='latitude',
            field=models.FloatField(help_text='Latitude of site origin (e.g. corner, centroid, etc., required)', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='site',
            name='longitude',
            field=models.FloatField(help_text='Longitude of site origin (e.g. corner, centroid, etc., required)', null=True, blank=True),
        ),
    ]
