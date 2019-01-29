from __future__ import absolute_import, unicode_literals, print_function, division
from django.conf import settings


def belongs_to(user, group_name):
    """
    Check if the user belongs to the given group.
    :param user:
    :param group_name:
    :return:
    """
    return user.groups.filter(name__iexact=group_name).exists()


def is_admin(user):
    return user.is_superuser or user.is_staff or belongs_to(user, 'Admins')


def can_create_user(user):
    """
    Only admin can create user except the server is set to allow public registration
    then anonymous user can create users
    :param user:
    :return:
    """
    if is_admin(user):
        return True
    else:
        return not user.is_authenticated and settings.ALLOW_PUBLIC_REGISTRATION
