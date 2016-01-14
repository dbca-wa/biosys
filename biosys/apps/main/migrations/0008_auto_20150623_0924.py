# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_site_accuracy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='tenure',
            field=models.CharField(default='', max_length=50, verbose_name='Tenure', blank=True, null=True),
            preserve_default=False,
        ),
    ]
