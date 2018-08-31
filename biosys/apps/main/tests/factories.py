from os import path
import factory
import base64

from django.contrib.auth import get_user_model

from main import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.sequence(lambda n: 'User{}'.format(n))


class ProgramFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Program

    name = factory.Sequence(lambda n: 'Program {}'.format(n))
    code = factory.Sequence(lambda n: 'PROGRAM{}'.format(n))


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Project

    name = factory.Sequence(lambda n: 'Project {}'.format(n))
    code = factory.Sequence(lambda n: 'PROJECT{}'.format(n))
    program = factory.SubFactory(ProgramFactory)


class SiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Site

    name = factory.Sequence(lambda n: 'Site {}'.format(n))
    code = factory.Sequence(lambda n: 'SITE{}'.format(n))


class DatasetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Dataset


CHUBBY_BAT_IMAGE_PATH = path.join(path.dirname(__file__), 'data/chubby-bat.png')


def get_chubby_bat_img_base64():
    """
    :return: bytes
    """
    with open(CHUBBY_BAT_IMAGE_PATH, 'rb') as fp:
        return base64.b64encode(fp.read())


class MediaFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Media

    file = factory.django.FileField(from_path=CHUBBY_BAT_IMAGE_PATH)


class ProjectMediaFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.ProjectMedia

    file = factory.django.FileField(from_path=CHUBBY_BAT_IMAGE_PATH)
    project = factory.SubFactory(ProjectFactory)


class DatasetMediaFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.DatasetMedia

    file = factory.django.FileField(from_path=CHUBBY_BAT_IMAGE_PATH)
    dataset = factory.SubFactory(DatasetFactory)
