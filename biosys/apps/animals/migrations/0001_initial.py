# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgeLookup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(max_length=500, verbose_name='Value')),
                ('code', models.CharField(max_length=10, verbose_name='Code', blank=True)),
                ('deprecated', models.BooleanField(default=False, verbose_name='Deprecated')),
            ],
            options={
                'ordering': ['value'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AnimalObservation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('collector', models.CharField(max_length=300, verbose_name='Collector', blank=True)),
                ('date', models.DateField(null=True, verbose_name='Observation Date', blank=True)),
                ('trap_no', models.CharField(max_length=20, verbose_name='Trap No', blank=True)),
                ('trap_type', models.CharField(max_length=30, verbose_name='Trap Type', blank=True)),
                ('bag_no', models.IntegerField(null=True, verbose_name='Bag No', blank=True)),
                ('microchip_id', models.CharField(max_length=30, verbose_name='Microchip number', blank=True)),
                ('tissue_number', models.CharField(max_length=30, verbose_name='DNA sample number', blank=True)),
                ('tissue_type', models.CharField(max_length=30, verbose_name='DNA sample type', blank=True)),
                ('voucher_number', models.CharField(max_length=30, verbose_name='Voucher', blank=True)),
                ('gross_weight', models.FloatField(help_text='Total weight of animal + bag (gms)', null=True, verbose_name='Gross weight (g)', blank=True)),
                ('bag_weight', models.FloatField(help_text='Total weight of bag (gms)', null=True, verbose_name='Bag weight (g)', blank=True)),
                ('net_weight', models.FloatField(null=True, verbose_name='Net weight (g)', blank=True)),
                ('head_length', models.IntegerField(null=True, verbose_name='Head length (mm)', blank=True)),
                ('pes_length', models.IntegerField(null=True, verbose_name='Pes length (mm)', blank=True)),
                ('liver_sample', models.CharField(max_length=10, verbose_name='Liver Sample', blank=True)),
                ('pouch', models.CharField(max_length=100, verbose_name='Pouch', blank=True)),
                ('test_length', models.CharField(max_length=100, verbose_name='Testes length', blank=True)),
                ('test_width', models.CharField(max_length=100, verbose_name='Testes width', blank=True)),
                ('svl', models.CharField(max_length=100, verbose_name='Head-Body', blank=True)),
                ('tail_length', models.CharField(max_length=50, verbose_name='Tail length', blank=True)),
                ('tail_condition', models.CharField(max_length=200, verbose_name='Tail condition', blank=True)),
                ('reproductive_condition', models.TextField(verbose_name='Reproductive condition', blank=True)),
                ('comments', models.TextField(verbose_name='Comments', blank=True)),
                ('age', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Age', to='animals.AgeLookup')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CaptureTypeLookup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(max_length=500, verbose_name='Value')),
                ('code', models.CharField(max_length=10, verbose_name='Code', blank=True)),
                ('deprecated', models.BooleanField(default=False, verbose_name='Deprecated')),
            ],
            options={
                'ordering': ['value'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ObservationTypeLookup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(max_length=500, verbose_name='Value')),
                ('code', models.CharField(max_length=10, verbose_name='Code', blank=True)),
                ('deprecated', models.BooleanField(default=False, verbose_name='Deprecated')),
            ],
            options={
                'ordering': ['value'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OpportunisticObservation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(null=True, verbose_name='Date', blank=True)),
                ('observer', models.CharField(max_length=100, verbose_name='Observer', blank=True)),
                ('latitude', models.FloatField(null=True, verbose_name='Latitude', blank=True)),
                ('longitude', models.FloatField(null=True, verbose_name='Longitude', blank=True)),
                ('datum', models.IntegerField(default=4326, null=True, verbose_name='Datum', blank=True, choices=[(4326, 'WGS84'), (4283, 'GDA94'), (4203, 'AGD84'), (4202, 'AGD66')])),
                ('comments', models.TextField(verbose_name='Comments', blank=True)),
                ('site_visit', models.ForeignKey(verbose_name='Site Visit', to='main.SiteVisit')),
                ('species', models.ForeignKey(verbose_name='Species', blank=True, to='main.SpeciesObservation', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SexLookup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(max_length=500, verbose_name='Value')),
                ('code', models.CharField(max_length=10, verbose_name='Code', blank=True)),
                ('deprecated', models.BooleanField(default=False, verbose_name='Deprecated')),
            ],
            options={
                'ordering': ['value'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Trap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('trapline_ID', models.CharField(max_length=50, null=True, verbose_name='Trap Line ID', blank=True)),
                ('open_date', models.DateField(null=True, verbose_name='Open Date', blank=True)),
                ('close_date', models.DateField(null=True, verbose_name='Close Date', blank=True)),
                ('start_latitude', models.FloatField(null=True, verbose_name='Start Latitude', blank=True)),
                ('start_longitude', models.FloatField(null=True, verbose_name='Start Longitude', blank=True)),
                ('stop_latitude', models.FloatField(null=True, verbose_name='Stop Latitude', blank=True)),
                ('stop_longitude', models.FloatField(null=True, verbose_name='Stop Longitude', blank=True)),
                ('traps_number', models.IntegerField(null=True, verbose_name='Number of Traps', blank=True)),
                ('datum', models.IntegerField(default=4326, null=True, verbose_name='Datum', blank=True, choices=[(4326, 'WGS84'), (4283, 'GDA94'), (4203, 'AGD84'), (4202, 'AGD66')])),
                ('comments', models.TextField(verbose_name='Comments', blank=True)),
                ('site_visit', models.ForeignKey(verbose_name='Site Visit', to='main.SiteVisit')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TrapTypeLookup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(max_length=500, verbose_name='Value')),
                ('code', models.CharField(max_length=10, verbose_name='Code', blank=True)),
                ('deprecated', models.BooleanField(default=False, verbose_name='Deprecated')),
            ],
            options={
                'ordering': ['value'],
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='trap',
            name='trap_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Trap Type', blank='', to='animals.TrapTypeLookup'),
        ),
        migrations.AddField(
            model_name='animalobservation',
            name='capture_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Capture Type', to='animals.CaptureTypeLookup'),
        ),
        migrations.AddField(
            model_name='animalobservation',
            name='sex',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Sex', to='animals.SexLookup'),
        ),
        migrations.AddField(
            model_name='animalobservation',
            name='site_visit',
            field=models.ForeignKey(verbose_name='Site Visit', to='main.SiteVisit'),
        ),
        migrations.AddField(
            model_name='animalobservation',
            name='species',
            field=models.ForeignKey(verbose_name='Species', to='main.SpeciesObservation'),
        ),
    ]
