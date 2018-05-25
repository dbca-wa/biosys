import factory

from main import models


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Project

    name = factory.Sequence(lambda n: 'Project {}'.format(n))
