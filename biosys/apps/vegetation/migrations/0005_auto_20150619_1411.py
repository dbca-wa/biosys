# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vegetation', '0004_auto_20150618_1350'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stratumspecies',
            name='condition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='vegetation.ConditionLookup', null=True),
        ),
    ]
