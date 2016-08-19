from __future__ import unicode_literals
from django.test import TestCase
from django.apps import apps
from django.conf import settings
from mixer.backend.django import mixer

from main.models import *
from main.utils import is_lookup_field


class TestGlobalAppModels(TestCase):
    def setUp(self):
        self.project_apps = [apps.get_app_config(app_name) for app_name in settings.PROJECT_APPS]
        self.project_models = []
        for app in self.project_apps:
            # Trick! we want to exclude the many to many intermediate table.
            # look for '_' in the name. Must be a better way.
            self.project_models += [m for m in app.models.values() if m._meta.model_name.find('_') < 0]
        self.project_fields = []
        for model in self.project_models:
            self.project_fields += model._meta.fields

    def test_lookups_fields_on_delete_protection(self):
        """
        Test that all the lookups foreign keys are set on_delete=PROTECTED
        """
        lookups_fields = [f for f in self.project_fields if is_lookup_field(f)]
        not_protected = [f for f in lookups_fields if f.remote_field.on_delete != models.PROTECT]
        self.assertTrue(len(not_protected) == 0,
                        msg="{} not protected on delete lookup field(s)."
                            " Should be 0. {}".format(len(not_protected),
                                                      str([(f.name, f.model) for f in not_protected])))

    def test_verbose_name_unique_within_model(self):
        """
        To avoid model parsing from XML insure that the verbose name of every field in a model is unique
        """
        for m in self.project_models:
            verbose_names = [f.verbose_name for f in m._meta.fields]
            self.assertEqual(len(verbose_names), len(set(verbose_names)),
                             msg="Some fields in the model {m} shared a verbose_name".format(m=m))

    def test_verbose_name_no_trailer_space(self):
        """
        I know it can cause problem to have a trailer whitespace at the end of a verbose name (column header)
        """
        for m in self.project_models:
            verbose_names = [f.verbose_name for f in m._meta.fields]
            for vn in verbose_names:
                self.assertEqual(len(vn), len(vn.strip()),
                                 msg="The verbose_name {name} of model {m} should not have a trailer whitespace"
                                 .format(name=vn, m=m))


class TestProject(TestCase):
    def setUp(self):
        pass

    def test_project_title_unique(self):
        """
        Test that we can't create two project with the same title
        """
        self.assertEqual(0, Project.objects.count())
        title = "Project#1"
        p1 = Project(title=title)
        p1.save()
        p2 = Project(title=title)
        with self.assertRaises(Exception):
            p2.save()


class TestSite(TestCase):
    def setUp(self):
        self.project = Project(title="UTest#1")
        self.project.save()

    def test_site_code_unique_within_project(self):
        """
        Test that a site with the same code can be created on  different project but not on the same project
        """
        project1 = self.project
        project2 = Project(title="jshdsakjdhsadkjah")
        project2.save()
        site1 = Site(
            project=project1,
            site_ID=1000,
            site_code="Site 001",
        )
        site1.save()
        # same code on different project
        site2 = Site(
            project=project2,
            site_ID=site1.site_ID + 1,
            site_code=site1.site_code,
        )
        try:
            site2.save()
        except Exception as e:
            self.assertFalse(True,
                             "Same site code on a different project should not throw an exception:{}".format(str(e)))

        # same code on same project, should throw an exception
        site2.site_code = site1.site_code
        site2.project = site1.project
        with self.assertRaises(Exception):
            site2.save()

    def test_geometry_created(self):
        """
        Test that a geometry is created when the site is saved
        This doesn't test the validity of the geometry
        """
        site = Site(
            project=self.project,
            site_ID=1000,
            site_code="Site 001",
        )
        site.save()
        self.assertIsNone(site.geometry)
        site.latitude = -18.0
        site.longitude = 125.0
        site.save()
        self.assertIsNotNone(site.geometry)