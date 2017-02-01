from rest_framework.authentication import SessionAuthentication


class NoCsrfSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        """Don't check csrf"""
        pass
