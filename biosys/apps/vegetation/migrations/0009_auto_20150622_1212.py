# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vegetation', '0008_auto_20150622_1108'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pegobservation',
            name='crust',
            field=models.FloatField(default=0.0, null=True, verbose_name='Crust', blank=True),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='erosion',
            field=models.FloatField(default=0.0, null=True, verbose_name='Erosion pegs', blank=True),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='frag_decay',
            field=models.FloatField(default=0.0, null=True, verbose_name='Fragm. and decaying', blank=True),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='intact_litter',
            field=models.FloatField(default=0.0, null=True, verbose_name='Intact Litter (mm)', blank=True),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='organic',
            field=models.FloatField(default=0.0, null=True, verbose_name='Organic mineral layer', blank=True),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='worm',
            field=models.FloatField(default=0.0, null=True, verbose_name='Worm cast layer', blank=True),
        ),
    ]
