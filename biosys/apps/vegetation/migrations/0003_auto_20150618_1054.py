# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vegetation', '0002_auto_20150616_0936'),
    ]

    operations = [
        migrations.AlterField(
            model_name='erosionpeg',
            name='y_direction',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='to the', choices=[('', ''), ('left', 'Left'), ('right', 'Right')]),
        ),
    ]
