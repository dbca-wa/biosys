# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_20150618_0918'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='aspect',
            field=models.CharField(choices=[('N', 'N'), ('NNE', 'NNE'), ('NE', 'NE'), ('ENE', 'ENE'), ('E', 'E'), ('ESE', 'ESE'), ('SE', 'SE'), ('SSE', 'SSE'), ('S', 'S'), ('SSW', 'SSW'), ('SW', 'SW'), ('WSW', 'WSW'), ('W', 'W'), ('WNW', 'WNW'), ('NW', 'NW'), ('NNW', 'NNW')], max_length=10, blank=True, help_text='Compass bearing (e.g. N, SSE)', null=True, verbose_name='Aspect'),
        ),
    ]
