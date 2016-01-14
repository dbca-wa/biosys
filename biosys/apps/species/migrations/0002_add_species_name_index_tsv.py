# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.db.migrations.operations.base import Operation


class LoadExtension(Operation):

    reversible = True

    def __init__(self, name):
        self.name = name

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS {}".format(self.name))

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute("DROP EXTENSION {}".format(self.name))

    def describe(self):
        return "Creates extension {}".format(self.name)


class CreateGinIndex(Operation):

    reversible = True

    def __init__(self, name):
        self.name = name

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute("CREATE INDEX {} ON species_species USING gin(to_tsvector('english', species_name))".format(self.name)),

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute("DROP INDEX {}".format(self.name)),

    def describe(self):
        return "Creates index {}".format(self.name)


class Migration(migrations.Migration):

    dependencies = [
        ('species', '0001_initial'),
    ]

    operations = [
        LoadExtension("pg_trgm"),
        CreateGinIndex("species_species_name_index_tsv")
    ]
