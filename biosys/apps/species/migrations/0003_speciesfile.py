# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('species', '0002_add_species_name_index_tsv'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpeciesFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(upload_to='%Y/%m/%d')),
                ('uploaded_date', models.DateTimeField(auto_now_add=True)),
                ('validated', models.BooleanField(default=False, help_text=b'True if every species name in the file has been validated against Herbie', verbose_name=b'Validated')),
                ('comments', models.TextField(help_text=b'', verbose_name=b'Comments', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
