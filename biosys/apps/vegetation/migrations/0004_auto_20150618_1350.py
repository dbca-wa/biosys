# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vegetation', '0003_auto_20150618_1054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='erosionpeg',
            name='y_direction',
            field=models.CharField(default='', choices=[('', ''), ('left', 'Left'), ('right', 'Right')], max_length=10, blank=True, null=True, verbose_name='to the'),
        ),
    ]
