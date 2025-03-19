from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import ClienteSerializer, AdvogadoSerializer, ProcessoSerializer
from .models import Cliente, Advogado, Processo
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import action
from django.http import JsonResponse
from django.conf import settings
import json



class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    
        
    
class AdvogadoViewSet(viewsets.ModelViewSet):
    queryset = Advogado.objects.all()
    serializer_class = AdvogadoSerializer
    permission_classes = [IsAuthenticated]
    
    
class ProcessoViewSet(viewsets.ModelViewSet):
    queryset = Processo.objects.all()
    serializer_class = ProcessoSerializer
    permission_classes = [IsAuthenticated]
    
@csrf_exempt
@action(detail=True, methods=['post'])
def registrarAdv(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

    chave_recebida = request.headers.get(getattr(settings,'API_HEADER_NAME','X-Api-Key'))
    chave_esperada = str(getattr(settings,'API_SECRET_KEY',"chavesecreta123"))
    if chave_recebida != chave_esperada:
        return JsonResponse({'error': 'Chave de API inválida.'}, status=403)
    
    data = json.loads(request.body)
    nome = data.get('nome')
    rg = data.get('rg')
    cpf = data.get('cpf')
    sexo = data.get('sexo')
    email = data.get('email')
    senha = data.get('senha')
    
    if not nome or not email:
        return JsonResponse ({"error": "Nome e email são obrigatórios."}, status=400)
    
    advogado = Advogado.objects.create(
        nome=nome, 
        email=email,
        rg = rg, 
        cpf = cpf, 
        sexo = sexo
        )
    advogado.set_password(senha)
    advogado.save()
    return JsonResponse({'message': 'advogado registrado com sucesso'}, status=201)    