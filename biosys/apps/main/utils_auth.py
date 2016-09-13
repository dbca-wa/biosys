from __future__ import absolute_import, unicode_literals, print_function, division


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
