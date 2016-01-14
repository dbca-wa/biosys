# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vegetation', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='groundcoversummary',
            options={'verbose_name_plural': 'ground cover summaries'},
        ),
        migrations.AlterModelOptions(
            name='stratumsummary',
            options={'verbose_name_plural': 'stratum summaries'},
        ),
    ]
