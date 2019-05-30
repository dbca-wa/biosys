from rest_framework.throttling import SimpleRateThrottle
from django.contrib.auth.models import User


class UserLoginRateThrottle(SimpleRateThrottle):
    scope = 'auth'

    def get_cache_key(self, request, view):
        user = User.objects.filter(username=request.data.get('username'))
        ident = user[0].pk if user else self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
