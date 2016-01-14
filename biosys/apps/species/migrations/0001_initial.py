# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Species',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name_id', models.IntegerField(help_text=b'Unique species reference', verbose_name=b'Name ID')),
                ('species_name', models.CharField(max_length=256, db_index=True)),
                ('consv_code', models.CharField(help_text=b'', max_length=10, null=True, verbose_name=b'Conservation status', blank=True)),
                ('source', models.CharField(max_length=64, db_index=True)),
            ],
            options={
                'ordering': ['species_name'],
                'verbose_name_plural': 'species',
            },
        ),
    ]
