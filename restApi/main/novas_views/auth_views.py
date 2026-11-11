from rest_framework_simplejwt.views import TokenObtainPairView
from ..serializers import CustomTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.throttling import ScopedRateThrottle
import json
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt, csrf_protect
from django.utils.decorators import method_decorator
from ..models import Advogado
from ..emailSender import EmailSender
from django.conf import settings
from datetime import timedelta


@method_decorator(ensure_csrf_cookie, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    authentication_classes = []
    throttle_scope = 'login'
    throttle_classes = [ScopedRateThrottle]
    
    def post(self, request, *args, **kwargs):
        # Verifica o campo remember_me antes de processar o login
        remember_me = request.data.get('remember_me', False)
        
        # Ajusta dinamicamente a configuração do SimpleJWT
        from rest_framework_simplejwt.settings import api_settings
        original_lifetime = api_settings.REFRESH_TOKEN_LIFETIME
        
        if remember_me:
            api_settings.REFRESH_TOKEN_LIFETIME = timedelta(days=7)
        else:
            api_settings.REFRESH_TOKEN_LIFETIME = timedelta(hours=8)
        
        # Get the standard response from parent
        response = super().post(request, *args, **kwargs)
        
        # Restaura a configuração original
        api_settings.REFRESH_TOKEN_LIFETIME = original_lifetime
        
        # Extract tokens from response data
        access_token = response.data.get('access')
        refresh_token = response.data.get('refresh')
        
        if access_token and refresh_token:
            # Define refresh token lifetime for cookie based on remember_me
            if remember_me:
                refresh_lifetime_seconds = 7 * 24 * 60 * 60  # 7 dias em segundos
            else:
                refresh_lifetime_seconds = 8 * 60 * 60  # 8 horas em segundos
            
            print(f"DEBUG: remember_me={remember_me}, refresh_lifetime_seconds={refresh_lifetime_seconds}")
            
            # Create HTTP-only cookies
            # Access token cookie
            response.set_cookie(
                'access_token',
                access_token,
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                path='/',
                secure=settings.JWT_COOKIE_SECURE,
                httponly=True,
                samesite=settings.JWT_COOKIE_SAMESITE,
            )

            # Refresh token cookie
            response.set_cookie(
                'refresh_token',
                refresh_token,
                max_age=refresh_lifetime_seconds,
                path='/',
                secure=settings.JWT_COOKIE_SECURE,
                httponly=True,
                samesite=settings.JWT_COOKIE_SAMESITE,
            )
            del response.data['access']
            del response.data['refresh']
            if 'remember_me' in response.data:
                del response.data['remember_me']

        return response
    
   
@method_decorator(csrf_exempt, name='dispatch')
class ResetPasswordView(APIView):
    authentication_classes = []
    throttle_scope = 'password_reset'
    throttle_classes = [ScopedRateThrottle]
    def validate_reset_token(self, token: str)->bool:
        try:
            refresh = RefreshToken(token)
            if refresh.payload.get("purpose") != "reset_password":
                return False
            return True
        except TokenError:
            return False
    
    
    def post(self, request,token):
        data = json.loads(request.body)
        password = data.get('password')
        
        if len(password) < 12:
            return JsonResponse({'error': 'A senha deve ter no mínimo 12 caracteres'}, status=400)
        if not self.validate_reset_token(token):
            return JsonResponse({'error': 'Token inválido ou expirado.'}, status=401)
        try:
            refresh = RefreshToken(token)
        except TokenError:
            return JsonResponse({'error': 'Token inválido ou expirado.'}, status=401)
        advogado = refresh.payload['user_id']
        advogado = Advogado.objects.get(id=advogado)
        advogado.set_password(password)
        advogado.save()
        refresh.blacklist()
        return JsonResponse({'message': 'senha resetada com sucesso'}, status=201)

        
    
@method_decorator(csrf_exempt, name='dispatch')
class EmailRequestSenha(APIView):
    authentication_classes = []
    throttle_scope = 'password_reset'
    throttle_classes = [ScopedRateThrottle]

    def post(self,request):
        data = json.loads(request.body)
        email = data.get('email')
        user = Advogado.objects.filter(email=email).first()
        if not user:
            return JsonResponse({'message': 'Se o e-mail estiver cadastrado, você receberá as instruções.'}, status=201)
        refresh = RefreshToken.for_user(user)
        refresh["purpose"] = "reset_password" 
        emailSender = EmailSender(email)
        emailSender.startserver()
        message = f'CLIQUE NO LINK PARA RESETAR SUA SENHA: {settings.FRONTEND_URL}/recovery/newPassword/{refresh}'
        emailSender.sendMensage('Resetar Senha', message)
        return JsonResponse({'message': 'Se o e-mail estiver cadastrado, você receberá as instruções.'}, status=201)

        
    
class ValidateResetTokenView(APIView):
    authentication_classes = []

    def get(self, request, token):
        try:
            refresh = RefreshToken(token)
            if refresh.payload.get("purpose") != "reset_password":
                return JsonResponse({'valid': False}, status=200)
            return JsonResponse({'valid': True}, status=200)
        except TokenError:
            return JsonResponse({'valid': False}, status=200)


@method_decorator(ensure_csrf_cookie, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class CustomTokenRefreshView(APIView):
    """
    Custom token refresh view that reads refresh token from HTTP-only cookie
    and sets new access token in HTTP-only cookie
    """

    authentication_classes = []
    throttle_scope = 'token_refresh'
    throttle_classes = [ScopedRateThrottle]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return JsonResponse({'error': 'Refresh token não encontrado'}, status=401)
        
        try:
            serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
            serializer.is_valid(raise_exception=True)
            access_token = serializer.validated_data['access']
            new_refresh_token = serializer.validated_data['refresh']

            response = JsonResponse({'detail': 'Token renovado com sucesso.'})
            response.set_cookie(
                'access_token',
                access_token,
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                path='/',
                secure=settings.JWT_COOKIE_SECURE,
                httponly=True,
                samesite=settings.JWT_COOKIE_SAMESITE,
            )
            response.set_cookie(
                'refresh_token',
                new_refresh_token,
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                path='/',
                secure=settings.JWT_COOKIE_SECURE,
                httponly=True,
                samesite=settings.JWT_COOKIE_SAMESITE,
            )
            return response
        except TokenError:
            return JsonResponse({'error': 'Refresh token inválido ou expirado'}, status=401)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfTokenView(APIView):
    """
    Endpoint público para inicializar o cookie CSRF.
    Não requer autenticação.
    O Django envia o cookie csrftoken através de Set-Cookie.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return JsonResponse({
            "detail": "CSRF cookie set",
            "csrfToken": get_token(request),
        })
