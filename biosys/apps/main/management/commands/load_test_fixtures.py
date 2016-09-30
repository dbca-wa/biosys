from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Load the fixtures that the tests use.'

    fixtures = [
        'test-groups',
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-generic-records',
        'test-observations',
        'test-species-observations',
    ]

    def handle(self, *args, **options):
        for fixture in self.fixtures:
            print('load {}'.format(fixture))
            call_command('loaddata', fixture)

