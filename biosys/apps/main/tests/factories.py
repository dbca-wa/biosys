from os import path
import factory


from main import models


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Project

    name = factory.Sequence(lambda n: 'Project {}'.format(n))


CHUBBY_BAT_IMAGE_PATH = path.join(path.dirname(__file__), 'data/chubby-bat.png')


class MediaFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Media

    file = factory.django.FileField(from_path=CHUBBY_BAT_IMAGE_PATH)
