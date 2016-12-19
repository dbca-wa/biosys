from __future__ import unicode_literals

from django.test import TestCase

from main.models import *


class TestProject(TestCase):
    fixtures = [
        'test-users',
    ]

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
