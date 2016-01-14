# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import main.models
import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GeologyGroupLookup',
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
            name='GeologyLookup',
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
            name='LandformElementLookup',
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
            name='LandformPatternLookup',
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
            name='LocationLookup',
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
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=300, verbose_name='Title')),
                ('code', models.CharField(max_length=30, null=True, verbose_name='Code', blank=True)),
                ('custodian', models.CharField(max_length=100, null=True, verbose_name='Custodian', blank=True)),
                ('email', models.EmailField(max_length=254, null=True, verbose_name='Email', blank=True)),
                ('objectives', models.TextField(null=True, verbose_name='Objectives', blank=True)),
                ('methodology', models.TextField(null=True, verbose_name='Methodology', blank=True)),
                ('funding', models.TextField(null=True, verbose_name='Funding', blank=True)),
                ('duration', models.CharField(max_length=100, null=True, verbose_name='Duration', blank=True)),
                ('datum', models.IntegerField(default=4326, null=True, verbose_name='Default Datum', blank=True, choices=[(4326, 'WGS84'), (4283, 'GDA94'), (4203, 'AGD84'), (4202, 'AGD66')])),
                ('extent_lat_min', models.FloatField(null=True, verbose_name='Extent latitude min', blank=True)),
                ('extent_lat_max', models.FloatField(null=True, verbose_name='Extent latitude max', blank=True)),
                ('extent_long_min', models.FloatField(null=True, verbose_name='Extent longitude min', blank=True)),
                ('extent_long_max', models.FloatField(null=True, verbose_name='Extent longitude max', blank=True)),
                ('comments', models.TextField(null=True, verbose_name='Comments', blank=True)),
                ('geometry', django.contrib.gis.db.models.fields.GeometryField(srid=4326, null=True, verbose_name='Extent Geometry', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('site_ID', models.IntegerField(default=main.models._calculate_site_ID, help_text='Site ID from Scientific Site Register.', unique=True, verbose_name='Site ID')),
                ('site_code', models.CharField(help_text='Local site code must be unique to project', max_length=100, verbose_name='Site Code')),
                ('date_established', models.DateField(default=datetime.date.today, verbose_name='Date established')),
                ('latitude', models.FloatField(default=0.0, verbose_name='Latitude')),
                ('longitude', models.FloatField(default=0.0, verbose_name='Longitude')),
                ('datum', models.IntegerField(default=4326, verbose_name='Datum', choices=[(4326, 'WGS84'), (4283, 'GDA94'), (4203, 'AGD84'), (4202, 'AGD66')])),
                ('established_by', models.CharField(max_length=200, null=True, verbose_name='Established by', blank=True)),
                ('bearing', models.FloatField(help_text='Degrees (0 - 360)', null=True, verbose_name='Bearing', blank=True)),
                ('width', models.IntegerField(null=True, verbose_name='Width (m)', blank=True)),
                ('height', models.IntegerField(null=True, verbose_name='Height (m)', blank=True)),
                ('aspect', models.CharField(choices=[('N', 'N'), ('NE', 'NE'), ('E', 'E'), ('SE', 'SE'), ('S', 'S'), ('SW', 'SW'), ('W', 'W'), ('NW', 'NW')], max_length=10, blank=True, help_text='Compass bearings (e.g. N, SSE)', null=True, verbose_name='Aspect')),
                ('slope', models.SmallIntegerField(help_text='Degrees (0 - 90)', null=True, verbose_name='Slope', blank=True)),
                ('altitude', models.FloatField(help_text='Altitude, in metres', null=True, verbose_name='Altitude', blank=True)),
                ('radius', models.FloatField(help_text='Radius, in metres', null=True, verbose_name='Radius', blank=True)),
                ('locality_description', models.TextField(null=True, verbose_name='Locality description', blank=True)),
                ('closest_water_distance', models.IntegerField(null=True, verbose_name='Distance to closest water (m)', blank=True)),
                ('soil_colour', models.CharField(max_length=150, verbose_name='Soil colour', blank=True)),
                ('photos_taken', models.TextField(verbose_name='Photos Taken', blank=True)),
                ('historical_info', models.TextField(null=True, verbose_name='Historical information', blank=True)),
                ('comments', models.TextField(null=True, verbose_name='Comments', blank=True)),
                ('geometry', django.contrib.gis.db.models.fields.GeometryField(srid=4326, null=True, verbose_name='Geometry', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='SiteCharacteristic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('closest_water_distance', models.IntegerField(null=True, verbose_name='Distance to closest water (m)', blank=True)),
                ('soil_colour', models.CharField(max_length=150, verbose_name='Soil colour', blank=True)),
                ('comments', models.TextField(null=True, verbose_name='Comments', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='SiteVisit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_status', models.CharField(default='quarantined', max_length=30, verbose_name='Data Status', choices=[('quarantined', 'Quarantined'), ('approved', 'Approved'), ('invalid', 'Invalid')])),
            ],
        ),
        migrations.CreateModel(
            name='SiteVisitDataFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(upload_to='%Y/%m/%d')),
                ('uploaded_date', models.DateTimeField(auto_now_add=True)),
                ('site', models.ForeignKey(verbose_name='Site', blank=True, to='main.Site', null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='User', to=settings.AUTH_USER_MODEL, help_text='User that uploaded the file')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SiteVisitDataSheetTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(upload_to='%Y/%m/%d')),
                ('uploaded_date', models.DateTimeField(auto_now_add=True)),
                ('version', models.CharField(default='1.0', max_length=50, verbose_name='Template Version')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SoilColourLookup',
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
            name='SoilSurfaceTextureLookup',
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
            name='SpeciesObservation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('input_name', models.CharField(max_length=500, verbose_name='Species')),
                ('name_id', models.IntegerField(default=-1, help_text='The unique ID from the herbarium database', verbose_name='Name ID')),
                ('site_visit', models.ForeignKey(verbose_name='Site Visit', to='main.SiteVisit')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TenureLookup',
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
            name='VegetationGroupLookup',
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
            name='Visit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=150, verbose_name='Visit Name')),
                ('start_date', models.DateField(default=datetime.date.today, verbose_name='Start Date')),
                ('end_date', models.DateField(null=True, verbose_name='End Date', blank=True)),
                ('trap_nights', models.IntegerField(null=True, verbose_name='Trap Nights', blank=True)),
                ('comments', models.TextField(null=True, verbose_name='Comments', blank=True)),
                ('project', models.ForeignKey(verbose_name='Project', to='main.Project')),
                ('sites', models.ManyToManyField(to='main.Site', verbose_name='Sites')),
            ],
        ),
        migrations.CreateModel(
            name='WaterTypeLookup',
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
            model_name='sitevisitdatafile',
            name='visit',
            field=models.ForeignKey(verbose_name='Visit', to='main.Visit'),
        ),
        migrations.AddField(
            model_name='sitevisit',
            name='data_file',
            field=models.ForeignKey(verbose_name='Data File', to='main.SiteVisitDataFile'),
        ),
        migrations.AddField(
            model_name='sitevisit',
            name='site',
            field=models.ForeignKey(verbose_name='Site', to='main.Site'),
        ),
        migrations.AddField(
            model_name='sitevisit',
            name='visit',
            field=models.ForeignKey(verbose_name='Visit', to='main.Visit'),
        ),
        migrations.AddField(
            model_name='sitecharacteristic',
            name='closest_water_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Type of closest water', blank=True, to='main.WaterTypeLookup', null=True),
        ),
        migrations.AddField(
            model_name='sitecharacteristic',
            name='landform_element',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Landform element (20m radius)', blank=True, to='main.LandformElementLookup', null=True),
        ),
        migrations.AddField(
            model_name='sitecharacteristic',
            name='landform_pattern',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Landform pattern (300m radius)', blank=True, to='main.LandformPatternLookup', null=True),
        ),
        migrations.AddField(
            model_name='sitecharacteristic',
            name='site_visit',
            field=models.ForeignKey(verbose_name='Site Visit', blank=True, to='main.SiteVisit', null=True),
        ),
        migrations.AddField(
            model_name='sitecharacteristic',
            name='soil_surface_texture',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Soil surface texture', blank=True, to='main.SoilSurfaceTextureLookup', null=True),
        ),
        migrations.AddField(
            model_name='sitecharacteristic',
            name='underlaying_geology',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Underlaying geology', blank=True, to='main.GeologyLookup', null=True),
        ),
        migrations.AddField(
            model_name='site',
            name='closest_water_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Type of closest water', blank=True, to='main.WaterTypeLookup', null=True),
        ),
        migrations.AddField(
            model_name='site',
            name='geology_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Geology group', blank=True, to='main.GeologyGroupLookup', null=True),
        ),
        migrations.AddField(
            model_name='site',
            name='landform_element',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Landform element (20m radius)', blank=True, to='main.LandformElementLookup', null=True),
        ),
        migrations.AddField(
            model_name='site',
            name='landform_pattern',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Landform pattern (300m radius)', blank=True, to='main.LandformPatternLookup', null=True),
        ),
        migrations.AddField(
            model_name='site',
            name='location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Location', blank=True, to='main.LocationLookup', null=True),
        ),
        migrations.AddField(
            model_name='site',
            name='parent_site',
            field=models.ForeignKey(verbose_name='Parent Site', blank=True, to='main.Site', null=True),
        ),
        migrations.AddField(
            model_name='site',
            name='project',
            field=models.ForeignKey(verbose_name='Project', to='main.Project'),
        ),
        migrations.AddField(
            model_name='site',
            name='soil_surface_texture',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Soil surface texture', blank=True, to='main.SoilSurfaceTextureLookup', null=True),
        ),
        migrations.AddField(
            model_name='site',
            name='tenure',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Tenure', blank=True, to='main.TenureLookup', null=True),
        ),
        migrations.AddField(
            model_name='site',
            name='underlaying_geology',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Underlaying geology', blank=True, to='main.GeologyLookup', null=True),
        ),
        migrations.AddField(
            model_name='site',
            name='vegetation_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Vegetation group', blank=True, to='main.VegetationGroupLookup', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='site',
            unique_together=set([('project', 'site_code')]),
        ),
    ]
