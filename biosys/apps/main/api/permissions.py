from django.conf import settings
from rest_framework.permissions import BasePermission

from main.api.views import is_data_engineer
from main.utils_auth import is_admin


class CanViewSwagger(BasePermission):
    """
    Since OEH Koala pen testing, Swagger should not be visible by user that has register freely on Biosys.
    Until we add a proper permission model for 'public' user we just restrict it to admin and data engineer if the
    server is set to allow public registration
    """
    # TODO: change permission when 'public' user model is implemented.
    def has_permission(self, request, view):
        if settings.ALLOW_PUBLIC_REGISTRATION:
            return request.user and (is_admin(request.user) or is_data_engineer(request.user))
        else:
            # authenticated
            return request.user and request.user.is_authenticated
