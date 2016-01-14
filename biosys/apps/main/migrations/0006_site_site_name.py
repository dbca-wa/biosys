# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_remove_site_locality_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='site_name',
            field=models.CharField(help_text='Enter a more descriptive name for this site, if one exists.', max_length=150, verbose_name='Site Name', blank=True),
        ),
    ]
