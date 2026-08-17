from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import CSRFCheck
from rest_framework import exceptions


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom authentication that reads JWT tokens from HTTP-only cookies and
    enforces Django's CSRF validation for authenticated cookie requests.
    """
    
    def get_header(self, request):
        access_token = request.COOKIES.get('access_token')
        if access_token:
            return f'Bearer {access_token}'.encode()

        return None

    def authenticate(self, request):
        authenticated = super().authenticate(request)
        if authenticated is not None:
            self.enforce_csrf(request)
        return authenticated

    @staticmethod
    def enforce_csrf(request):
        check = CSRFCheck(lambda request: None)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied(f'CSRF Failed: {reason}')
