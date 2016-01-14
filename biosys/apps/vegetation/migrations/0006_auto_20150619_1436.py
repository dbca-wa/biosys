# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vegetation', '0005_auto_20150619_1411'),
    ]

    operations = [
        migrations.AlterField(
            model_name='disturbanceindicator',
            name='camels',
            field=models.ForeignKey(related_name='camels_evidence', on_delete=django.db.models.deletion.PROTECT, verbose_name='Camels', blank=True, to='vegetation.FeralEvidenceLookup', null=True),
        ),
        migrations.AlterField(
            model_name='disturbanceindicator',
            name='cats',
            field=models.ForeignKey(related_name='cats_evidence', on_delete=django.db.models.deletion.PROTECT, verbose_name='Cats', blank=True, to='vegetation.FeralEvidenceLookup', null=True),
        ),
        migrations.AlterField(
            model_name='disturbanceindicator',
            name='cattle_dung',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Cattle Dung', blank=True, to='vegetation.CattleDungLookup', null=True),
        ),
        migrations.AlterField(
            model_name='disturbanceindicator',
            name='cattle_sighted',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Cattle sighted', blank=True, to='vegetation.CattleSightedLookup', null=True),
        ),
        migrations.AlterField(
            model_name='disturbanceindicator',
            name='evidence_recent_fire',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Evidence of recent Fire', blank=True, to='vegetation.EvidenceRecentFireLookup', null=True),
        ),
        migrations.AlterField(
            model_name='disturbanceindicator',
            name='fire_intensity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Fire Intensity', blank=True, to='vegetation.FireIntensityLookup', null=True),
        ),
        migrations.AlterField(
            model_name='disturbanceindicator',
            name='grazing_level',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Grazing Level', blank=True, to='vegetation.GrazingLevelLookup', null=True),
        ),
        migrations.AlterField(
            model_name='disturbanceindicator',
            name='horses_donkeys',
            field=models.ForeignKey(related_name='horses_donkeys_evidence', on_delete=django.db.models.deletion.PROTECT, verbose_name='Horses/ Donkeys', blank=True, to='vegetation.FeralEvidenceLookup', null=True),
        ),
        migrations.AlterField(
            model_name='disturbanceindicator',
            name='pigs',
            field=models.ForeignKey(related_name='pigs_evidence', on_delete=django.db.models.deletion.PROTECT, verbose_name='Pigs', blank=True, to='vegetation.FeralEvidenceLookup', null=True),
        ),
        migrations.AlterField(
            model_name='disturbanceindicator',
            name='recently_burned_percent',
            field=models.IntegerField(default=0, null=True, verbose_name='Recently Burned Veg in %', blank=True),
        ),
        migrations.AlterField(
            model_name='disturbanceindicator',
            name='scorch_height',
            field=models.IntegerField(default=0, null=True, verbose_name='Scorch Height m', blank=True),
        ),
        migrations.AlterField(
            model_name='disturbanceindicator',
            name='signs_damage_percent',
            field=models.IntegerField(default=0, null=True, verbose_name='Veg affected within Site %', blank=True),
        ),
        migrations.AlterField(
            model_name='disturbanceindicator',
            name='tracks_trampling',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Tracks and Trampling', blank=True, to='vegetation.TracksTramplingLookup', null=True),
        ),
    ]
