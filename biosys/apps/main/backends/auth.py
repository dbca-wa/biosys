import requests
from confy import env
from django.contrib.auth import get_user_model

UserModel = get_user_model()

ASMS_LOGIN_URL = env('ASMS_LOGIN_URL', "https://environment.nsw.gov.au/asmslightprofileapp/account/login")


class OEHBackend(object):
    """
    Connect to the OEH ASMS login page and check the user credentials.
    """
    user_model = get_user_model()

    @staticmethod
    def asms_login_valid(username, password):
        payload = {
            'UserName': username,
            'Password': password
        }
        response = requests.post(ASMS_LOGIN_URL, data=payload)
        # to test for success look for a redirection.
        has_redirection = False
        if response.history and response.history[0].status_code in [301, 302]:
            has_redirection = True
        return response.status_code == 200 and has_redirection

    def authenticate(self, request, username=None, password=None):
        asms_valid = self.asms_login_valid(username, password)
        user = None
        if asms_valid:
            user, _ = UserModel.objects.get_or_create(username=username)
            # update password every time.
            user.set_password(password)
            user.save()
        return user

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
