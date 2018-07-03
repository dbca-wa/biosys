from __future__ import unicode_literals

from django.test import TestCase

from main.models import *

from main.tests import factories


class TestProject(TestCase):

    def test_project_name_unique(self):
        """
        Test that we can't create two project with the same name
        """
        self.assertEqual(0, Project.objects.count())
        program = factories.ProgramFactory.create()
        name = "Project#1"
        p1 = Project(program=program, name=name)
        p1.save()
        p2 = Project(program=program, name=name)
        with self.assertRaises(Exception):
            p2.save()


class TestSite(TestCase):
    def setUp(self):
        self.program = factories.ProgramFactory.create()
        self.project = factories.ProjectFactory.create(program=self.program)

    def test_site_code_unique_within_project(self):
        """
        Test that a site with the same code can be created on  different project but not on the same project
        """
        project1 = self.project
        project2 = Project(name="jshdsakjdhsadkjah", program=self.program)
        project2.save()
        site1 = Site(
            project=project1,
            code="Site 001",
        )
        site1.save()
        # same code on different project
        site2 = Site(
            project=project2,
            code=site1.code,
        )
        try:
            site2.save()
        except Exception as e:
            self.assertFalse(True,
                             "Same site code on a different project should not throw an exception:{}".format(str(e)))

        # same code on same project, should throw an exception
        site2.code = site1.code
        site2.project = site1.project
        with self.assertRaises(Exception):
            site2.save()
