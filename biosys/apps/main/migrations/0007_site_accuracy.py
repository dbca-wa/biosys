# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_site_site_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='accuracy',
            field=models.FloatField(default=30.0, verbose_name='Accuracy (m)'),
        ),
    ]
