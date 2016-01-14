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
            name='BasalBitterlichObservation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('basal_area', models.IntegerField(null=True, verbose_name='Basal Area', blank=True)),
                ('bitterlich_trees', models.IntegerField(null=True, verbose_name='Bitterlich (trees)', blank=True)),
                ('bitterlich_shrubs', models.IntegerField(null=True, verbose_name='Bitterlich (shrubs)', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='BiodiversityIndicator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comments', models.TextField(verbose_name='Comments', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='BiodiversityIndicatorLookup',
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
            name='CattleDungLookup',
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
            name='CattleSightedLookup',
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
            name='ConditionLookup',
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
            name='DisturbanceIndicator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('recently_burned_percent', models.IntegerField(default=0, verbose_name='Recently Burned Veg in %')),
                ('scorch_height', models.IntegerField(default=0, verbose_name='Scorch Height m')),
                ('signs_damage_percent', models.IntegerField(default=0, verbose_name='Veg affected within Site %')),
                ('weed_percent', models.FloatField(default=0, null=True, verbose_name='Veg consisting of Weeds in %', blank=True)),
                ('comments', models.TextField(verbose_name='Comments', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ErosionPeg',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('peg_ID', models.CharField(default='A', max_length=20, verbose_name='Peg ID')),
                ('transect_x', models.FloatField(verbose_name='at ... m on transect')),
                ('transect_y', models.FloatField(verbose_name='walk ... m')),
                ('y_direction', models.CharField(max_length=10, null=True, verbose_name='to the')),
            ],
        ),
        migrations.CreateModel(
            name='EvidenceRecentFireLookup',
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
            name='FeralEvidenceLookup',
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
            name='FireIntensityLookup',
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
            name='GrazingLevelLookup',
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
            name='GroundCoverSummary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('perennial_grass', models.FloatField(null=True, verbose_name='Perennial Grass %', blank=True)),
                ('annual_grass', models.FloatField(null=True, verbose_name='Annual Grass %', blank=True)),
                ('herb', models.FloatField(null=True, verbose_name='Herb %', blank=True)),
                ('litter', models.FloatField(null=True, verbose_name='Litter %', blank=True)),
                ('logs', models.FloatField(null=True, verbose_name='Logs (>50mm) %', blank=True)),
                ('rock_gravel', models.FloatField(null=True, verbose_name='Exposed Rock and Gravel %', blank=True)),
                ('bare_ground', models.FloatField(null=True, verbose_name='Bare Ground %', blank=True)),
                ('termite_mound', models.FloatField(null=True, verbose_name='Termite Mound %', blank=True)),
                ('comments', models.TextField(verbose_name='Comments', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PegObservation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('peg_ID', models.CharField(default='A', max_length=20, verbose_name='Peg ID')),
                ('intact_litter', models.PositiveIntegerField(default=0, verbose_name='Intact Litter (mm)')),
                ('frag_decay', models.PositiveIntegerField(default=0, verbose_name='Fragm. and decaying')),
                ('crust', models.PositiveIntegerField(default=0, verbose_name='Crust')),
                ('worm', models.PositiveIntegerField(default=0, verbose_name='Worm cast layer')),
                ('organic', models.PositiveIntegerField(default=0, verbose_name='Organic mineral layer')),
                ('erosion', models.PositiveIntegerField(default=0, verbose_name='Erosion pegs')),
            ],
        ),
        migrations.CreateModel(
            name='PlantObservation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('introduced', models.BooleanField(default=False, verbose_name='Introduced')),
                ('extent', models.CharField(max_length=200, verbose_name='Extent of Infestation', blank=True)),
                ('density', models.CharField(max_length=50, verbose_name='Density', blank=True)),
                ('invasiveness', models.CharField(max_length=50, verbose_name='Invasiveness', blank=True)),
                ('species', models.ForeignKey(verbose_name='Species', blank=True, to='main.SpeciesObservation', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SignificanceLookup',
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
            name='StratumLookup',
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
            name='StratumSpecies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('collector_no', models.CharField(max_length=30, verbose_name='Collector No', blank=True)),
                ('avg_height', models.FloatField(verbose_name='Average Height (m)')),
                ('cover', models.FloatField(null=True, verbose_name='Cover %', blank=True)),
                ('basal_area', models.FloatField(null=True, verbose_name='Basal Area', blank=True)),
                ('bitterlich_cover', models.FloatField(null=True, verbose_name='Bitterlich % cover', blank=True)),
                ('juv_lt_2m', models.BooleanField(default=False, verbose_name='Juvenile <2m')),
                ('juv_mt_2m', models.BooleanField(default=False, verbose_name='Juvenile >2m')),
                ('adult', models.BooleanField(default=False, verbose_name='Adult')),
                ('mature', models.BooleanField(default=False, verbose_name='Mature (at peak of prod.)')),
                ('flowering', models.BooleanField(default=False, verbose_name='Flowering')),
                ('fruiting', models.BooleanField(default=False, verbose_name='Fruiting')),
                ('seeding', models.BooleanField(default=False, verbose_name='Seeding')),
                ('comments', models.TextField(verbose_name='Comments', blank=True)),
                ('condition', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Condition', to='vegetation.ConditionLookup')),
                ('significance', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Significance', blank=True, to='vegetation.SignificanceLookup', null=True)),
                ('species', models.ForeignKey(verbose_name='Species', blank=True, to='main.SpeciesObservation', null=True)),
                ('stratum', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Stratum', to='vegetation.StratumLookup')),
            ],
            options={
                'verbose_name_plural': 'stratum species',
            },
        ),
        migrations.CreateModel(
            name='StratumSummary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('growth_form', models.CharField(max_length=100, verbose_name='Growth Form')),
                ('crown_cover', models.FloatField(verbose_name='% Cover (Crown Cover)')),
                ('avg_height', models.FloatField(verbose_name='Average Height (m)')),
                ('max_height', models.FloatField(verbose_name='Maximum Height (m)')),
                ('stratum', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Stratum', to='vegetation.StratumLookup')),
            ],
        ),
        migrations.CreateModel(
            name='TracksTramplingLookup',
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
            name='TransectDistinctChanges',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('point_of_change', models.FloatField(null=True, verbose_name='Point of Change (m.cm)', blank=True)),
                ('change_from', models.CharField(max_length=150, verbose_name='Change from', blank=True)),
                ('change_to', models.CharField(max_length=150, verbose_name='Change to', blank=True)),
            ],
            options={
                'verbose_name_plural': 'transect distinct changes',
            },
        ),
        migrations.CreateModel(
            name='TransectObservation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('perennial_grass', models.FloatField(null=True, verbose_name='Perennial Grass %', blank=True)),
                ('annual_grass', models.FloatField(null=True, verbose_name='Annual Grass %', blank=True)),
                ('herb', models.FloatField(null=True, verbose_name='Herb %', blank=True)),
                ('litter', models.FloatField(null=True, verbose_name='Litter %', blank=True)),
                ('logs', models.FloatField(null=True, verbose_name='Logs (>50mm) %', blank=True)),
                ('rock_gravel', models.FloatField(null=True, verbose_name='Exposed Rock and Gravel %', blank=True)),
                ('bare_ground', models.FloatField(null=True, verbose_name='Bare Ground %', blank=True)),
                ('termite_mound', models.FloatField(null=True, verbose_name='Termite Mound %', blank=True)),
                ('low_shrub', models.FloatField(null=True, verbose_name='Woody Subshrub %', blank=True)),
                ('shrub', models.FloatField(null=True, verbose_name='Shrub %', blank=True)),
                ('tree', models.FloatField(null=True, verbose_name='Tree %', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='VegetationVisit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('collector', models.CharField(max_length=150, verbose_name='Vegetation collector', blank=True)),
                ('date', models.DateField(null=True, verbose_name='Visit Date', blank=True)),
                ('site_visit', models.ForeignKey(verbose_name='Site Visit', to='main.SiteVisit')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='transectobservation',
            name='vegetation_visit',
            field=models.ForeignKey(verbose_name='Vegetation Visit', to='vegetation.VegetationVisit'),
        ),
        migrations.AddField(
            model_name='transectdistinctchanges',
            name='vegetation_visit',
            field=models.ForeignKey(verbose_name='Vegetation Visit', to='vegetation.VegetationVisit'),
        ),
        migrations.AddField(
            model_name='stratumsummary',
            name='vegetation_visit',
            field=models.ForeignKey(verbose_name='Vegetation Visit', to='vegetation.VegetationVisit'),
        ),
        migrations.AddField(
            model_name='stratumspecies',
            name='vegetation_visit',
            field=models.ForeignKey(verbose_name='Vegetation Visit', to='vegetation.VegetationVisit'),
        ),
        migrations.AddField(
            model_name='plantobservation',
            name='vegetation_visit',
            field=models.ForeignKey(verbose_name='Vegetation Visit', to='vegetation.VegetationVisit'),
        ),
        migrations.AddField(
            model_name='pegobservation',
            name='vegetation_visit',
            field=models.ForeignKey(verbose_name='Vegetation Visit', to='vegetation.VegetationVisit'),
        ),
        migrations.AddField(
            model_name='groundcoversummary',
            name='vegetation_visit',
            field=models.ForeignKey(verbose_name='Vegetation Visit', to='vegetation.VegetationVisit'),
        ),
        migrations.AddField(
            model_name='erosionpeg',
            name='vegetation_visit',
            field=models.ForeignKey(verbose_name='Vegetation Visit', to='vegetation.VegetationVisit'),
        ),
        migrations.AddField(
            model_name='disturbanceindicator',
            name='camels',
            field=models.ForeignKey(related_name='camels_evidence', on_delete=django.db.models.deletion.PROTECT, verbose_name='Camels', to='vegetation.FeralEvidenceLookup'),
        ),
        migrations.AddField(
            model_name='disturbanceindicator',
            name='cats',
            field=models.ForeignKey(related_name='cats_evidence', on_delete=django.db.models.deletion.PROTECT, verbose_name='Cats', to='vegetation.FeralEvidenceLookup'),
        ),
        migrations.AddField(
            model_name='disturbanceindicator',
            name='cattle_dung',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Cattle Dung', to='vegetation.CattleDungLookup'),
        ),
        migrations.AddField(
            model_name='disturbanceindicator',
            name='cattle_sighted',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Cattle sighted', to='vegetation.CattleSightedLookup'),
        ),
        migrations.AddField(
            model_name='disturbanceindicator',
            name='evidence_recent_fire',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Evidence of recent Fire', to='vegetation.EvidenceRecentFireLookup'),
        ),
        migrations.AddField(
            model_name='disturbanceindicator',
            name='fire_intensity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Fire Intensity', to='vegetation.FireIntensityLookup'),
        ),
        migrations.AddField(
            model_name='disturbanceindicator',
            name='grazing_level',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Grazing Level', to='vegetation.GrazingLevelLookup'),
        ),
        migrations.AddField(
            model_name='disturbanceindicator',
            name='horses_donkeys',
            field=models.ForeignKey(related_name='horses_donkeys_evidence', on_delete=django.db.models.deletion.PROTECT, verbose_name='Horses/ Donkeys', to='vegetation.FeralEvidenceLookup'),
        ),
        migrations.AddField(
            model_name='disturbanceindicator',
            name='pigs',
            field=models.ForeignKey(related_name='pigs_evidence', on_delete=django.db.models.deletion.PROTECT, verbose_name='Pigs', to='vegetation.FeralEvidenceLookup'),
        ),
        migrations.AddField(
            model_name='disturbanceindicator',
            name='tracks_trampling',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Tracks and Trampling', to='vegetation.TracksTramplingLookup'),
        ),
        migrations.AddField(
            model_name='disturbanceindicator',
            name='vegetation_visit',
            field=models.ForeignKey(verbose_name='Vegetation Visit', to='vegetation.VegetationVisit'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='crevices',
            field=models.ForeignKey(related_name='crevices_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Rock Crevices', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='fauna_habitat',
            field=models.ForeignKey(related_name='fauna_habitat_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Fauna Habitat and Shelter', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='flowering',
            field=models.ForeignKey(related_name='flowering_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Flowering', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='food_avail',
            field=models.ForeignKey(related_name='food_avail_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Food Availability', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='fruiting',
            field=models.ForeignKey(related_name='fruiting_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Fruiting', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='logs',
            field=models.ForeignKey(related_name='logs_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Logs', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='others',
            field=models.ForeignKey(related_name='others_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Other Signs', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='scats',
            field=models.ForeignKey(related_name='scats_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Scats', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='seeding',
            field=models.ForeignKey(related_name='seeding_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Seeding', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='sightings',
            field=models.ForeignKey(related_name='sightings_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Sightings', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='termites',
            field=models.ForeignKey(related_name='termites_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Termite Mounds', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='traces',
            field=models.ForeignKey(related_name='traces_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Tracks and Traces', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='tracks',
            field=models.ForeignKey(related_name='tracks_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Tracks', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='tree_hollows',
            field=models.ForeignKey(related_name='tree_hollows_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Tree Hollows', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='veg_cover',
            field=models.ForeignKey(related_name='veg_cover_indicator', on_delete=django.db.models.deletion.PROTECT, verbose_name='Veg Cover', to='vegetation.BiodiversityIndicatorLookup'),
        ),
        migrations.AddField(
            model_name='biodiversityindicator',
            name='vegetation_visit',
            field=models.ForeignKey(verbose_name='Vegetation Visit', to='vegetation.VegetationVisit'),
        ),
        migrations.AddField(
            model_name='basalbitterlichobservation',
            name='vegetation_visit',
            field=models.ForeignKey(verbose_name='Vegetation Visit', to='vegetation.VegetationVisit'),
        ),
    ]
