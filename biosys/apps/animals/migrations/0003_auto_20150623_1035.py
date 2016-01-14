# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('animals', '0002_auto_20150618_1642'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='animalobservation',
            name='bag_no',
        ),
        migrations.RemoveField(
            model_name='animalobservation',
            name='liver_sample',
        ),
        migrations.RemoveField(
            model_name='animalobservation',
            name='voucher_number',
        ),
        migrations.AddField(
            model_name='animalobservation',
            name='fate',
            field=models.CharField(default='', choices=[('', ''), ('released', 'released'), ('vouchered', 'vouchered'), ('accidental death', 'accidental death')], max_length=30, blank=True, help_text='What happened to animal after trapping', verbose_name='Fate'),
        ),
        migrations.AlterField(
            model_name='animalobservation',
            name='pouch',
            field=models.CharField(default='', max_length=100, verbose_name='Pouch', blank=True, choices=[('', ''), ('teats', 'teats'), ('pouch young', 'pouch young')]),
        ),
        migrations.AlterField(
            model_name='animalobservation',
            name='reproductive_condition',
            field=models.CharField(default='', max_length=20, verbose_name='Reproductive condition', blank=True, choices=[('', ''), ('developed', 'developed')]),
        ),
        migrations.AlterField(
            model_name='animalobservation',
            name='tail_condition',
            field=models.CharField(default='', max_length=200, verbose_name='Tail condition', blank=True, choices=[('', ''), ('regrowth', 'regrowth'), ('partially missing', 'partially missing'), ('missing', 'missing')]),
        ),
        migrations.AlterField(
            model_name='animalobservation',
            name='tissue_number',
            field=models.CharField(help_text='Enter the sample number (e.g. tag number, DNA sample number)', max_length=30, verbose_name='Sample number', blank=True),
        ),
        migrations.AlterField(
            model_name='animalobservation',
            name='tissue_type',
            field=models.CharField(help_text='Enter DNA sample type (e.g. earclip, scute clip, hair sample)', max_length=30, verbose_name='DNA sample type', blank=True),
        ),
    ]
