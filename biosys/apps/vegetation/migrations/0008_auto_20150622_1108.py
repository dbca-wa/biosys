# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('vegetation', '0007_auto_20150622_0841'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pegobservation',
            name='crust',
            field=models.FloatField(default=0.0, null=True, verbose_name='Crust', blank=True, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='erosion',
            field=models.FloatField(default=0.0, null=True, verbose_name='Erosion pegs', blank=True, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='frag_decay',
            field=models.FloatField(default=0.0, null=True, verbose_name='Fragm. and decaying', blank=True, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='intact_litter',
            field=models.FloatField(default=0.0, null=True, verbose_name='Intact Litter (mm)', blank=True, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='organic',
            field=models.FloatField(default=0.0, null=True, verbose_name='Organic mineral layer', blank=True, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='pegobservation',
            name='worm',
            field=models.FloatField(default=0.0, null=True, verbose_name='Worm cast layer', blank=True, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
    ]
