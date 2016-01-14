# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='code',
            field=models.CharField(help_text='Provide a brief code or acronym for this project. This code could be used for prefixing site codes.', max_length=30, null=True, verbose_name='Code', blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='custodian',
            field=models.CharField(help_text='The person responsible for the content of this project.', max_length=100, null=True, verbose_name='Custodian', blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='datum',
            field=models.IntegerField(default=4326, choices=[(4326, 'WGS84'), (4283, 'GDA94'), (4203, 'AGD84'), (4202, 'AGD66')], blank=True, help_text='The datum all locations will be assumed to have unless otherwise specified.', null=True, verbose_name='Default Datum'),
        ),
        migrations.AlterField(
            model_name='project',
            name='duration',
            field=models.CharField(help_text='The likely duration of the project.', max_length=100, null=True, verbose_name='Duration', blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='extent_lat_max',
            field=models.FloatField(help_text='The northernmost extent of the project (-90 - 0)', null=True, verbose_name='Extent latitude max', blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='extent_lat_min',
            field=models.FloatField(help_text='The southernmost extent of the project (-90 - 0)', null=True, verbose_name='Extent latitude min', blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='extent_long_max',
            field=models.FloatField(help_text='The easternmost extent of the project (0 - 180)', null=True, verbose_name='Extent longitude max', blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='extent_long_min',
            field=models.FloatField(help_text='The westernmost extent of the project (0 - 180)', null=True, verbose_name='Extent longitude min', blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='title',
            field=models.CharField(help_text='Enter a brief title for the project (required).', unique=True, max_length=300, verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='site',
            name='aspect',
            field=models.CharField(choices=[('N', 'N'), ('NE', 'NE'), ('E', 'E'), ('SE', 'SE'), ('S', 'S'), ('SW', 'SW'), ('W', 'W'), ('NW', 'NW')], max_length=10, blank=True, help_text='Compass bearing (e.g. N, SSE)', null=True, verbose_name='Aspect'),
        ),
        migrations.AlterField(
            model_name='site',
            name='date_established',
            field=models.DateField(default=datetime.date.today, help_text='The date this site was first established (required)', verbose_name='Date established'),
        ),
        migrations.AlterField(
            model_name='site',
            name='latitude',
            field=models.FloatField(default=0.0, help_text='Latitude of site origin (e.g. corner, centroid, etc., required)', verbose_name='Latitude'),
        ),
        migrations.AlterField(
            model_name='site',
            name='longitude',
            field=models.FloatField(default=0.0, help_text='Longitude of site origin (e.g. corner, centroid, etc., required)', verbose_name='Longitude'),
        ),
        migrations.AlterField(
            model_name='site',
            name='parent_site',
            field=models.ForeignKey(blank=True, to='main.Site', help_text="Sites can be grouped together. If you have a subregion within the project that contains a number of sites, create that region as a parent site first, then select that parent when you're creating this site.", null=True, verbose_name='Parent Site'),
        ),
        migrations.AlterField(
            model_name='site',
            name='project',
            field=models.ForeignKey(verbose_name='Project', to='main.Project', help_text='Select the project this site is part of (required)'),
        ),
        migrations.AlterField(
            model_name='site',
            name='site_code',
            field=models.CharField(help_text='Local site code must be unique to this project. e.g. LCI123 (required)', max_length=100, verbose_name='Site Code'),
        ),
        migrations.AlterField(
            model_name='visit',
            name='end_date',
            field=models.DateField(help_text='Enter the actual end date of the visit', null=True, verbose_name='End Date', blank=True),
        ),
        migrations.AlterField(
            model_name='visit',
            name='name',
            field=models.CharField(help_text='Enter a unique name for this visit to the sites listed above (required)', max_length=150, verbose_name='Visit Name'),
        ),
        migrations.AlterField(
            model_name='visit',
            name='start_date',
            field=models.DateField(default=datetime.date.today, help_text='Enter the start date of the visit (required)', verbose_name='Start Date'),
        ),
        migrations.AlterField(
            model_name='visit',
            name='trap_nights',
            field=models.IntegerField(help_text='Enter the number of actual trapping nights that occurred.', null=True, verbose_name='Trap Nights', blank=True),
        ),
    ]
