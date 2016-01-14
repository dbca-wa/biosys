# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vegetation', '0006_auto_20150619_1436'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pegobservation',
            name='crust',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name='Crust', blank=True),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='erosion',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name='Erosion pegs', blank=True),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='frag_decay',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name='Fragm. and decaying', blank=True),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='intact_litter',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name='Intact Litter (mm)', blank=True),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='organic',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name='Organic mineral layer', blank=True),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='peg_ID',
            field=models.CharField(default='A', max_length=20, null=True, verbose_name='Peg ID', blank=True),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='worm',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name='Worm cast layer', blank=True),
        ),
    ]
