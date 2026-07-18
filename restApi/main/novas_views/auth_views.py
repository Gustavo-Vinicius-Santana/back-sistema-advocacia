from rest_framework_simplejwt.views import TokenObtainPairView
from ..serializers import CustomTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from jwt.exceptions import InvalidTokenError
import json
from django.http import JsonResponse
from ..models import Advogado
from ..emailSender import EmailSender


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    
    @classmethod
    def get_token(cls, advogado):
        token = super().get_token(advogado)
        
        # Adicione as informações do advogado ao token
        token['advogado_id'] = advogado.id
        token['advogado_nome'] = advogado.nome
        token['advogado_email'] = advogado.email
        advogado.is_online = True
        advogado.save()
        
             
        return token
    
   
class ResetPasswordView(APIView):
    def validate_reset_token(self, token: str)->bool:
        try:
            refresh = RefreshToken(token)
            if refresh.payload.get("purpose") != "reset_password":
                return False
            return True
        except InvalidTokenError:
            return False
    
    
    def post(self, request,token):
        data = json.loads(request.body)
        password = data.get('password')
        if not self.validate_reset_token(token):
            return JsonResponse({'error': 'Token inválido ou expirado.'}, status=401)
        try:
            refresh = RefreshToken(token)
        except InvalidTokenError:
            return JsonResponse({'error': 'Token inválido ou expirado.'}, status=401)
        advogado = refresh.payload['user_id']
        advogado = Advogado.objects.get(id=advogado)
        advogado.set_password(password)
        advogado.save()
        refresh.blacklist()
        return JsonResponse({'message': 'senha resetada com sucesso'}, status=201)

        
    
class EmailRequestSenha(APIView):
    def post(self,request):
        data = json.loads(request.body)
        email = data.get('email')
        user = Advogado.objects.filter(email=email).first()
        refresh = RefreshToken.for_user(user)
        refresh["purpose"] = "reset_password" 
        print(refresh)
        emailSender = EmailSender(email)
        emailSender.startserver()
        message =f'CLIQUE NO LINK PARA RESETAR SUA SENHA: http://127.0.0.1:3000/recovery/newPassword/{refresh}'
        emailSender.sendMensage('Resetar Senha', message)
        return JsonResponse({'message': 'email enviado com sucesso'}, status=201)

        
    
class ValidateResetTokenView(APIView):
    def get(self, request, token):
        try:
            refresh = RefreshToken(token)
            if refresh.payload.get("purpose") != "reset_password":
                return JsonResponse({'valid': False}, status=200)
            return JsonResponse({'valid': True}, status=200)
        except InvalidTokenError:
            return JsonResponse({'valid': False}, status=200)
    