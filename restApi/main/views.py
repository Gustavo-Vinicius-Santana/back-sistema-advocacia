from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import ClienteSerializer, AdvogadoSerializer, ProcessoSerializer,TarefasSerializer,AdvogadoResumidoSerializer,ProcesssosResumidoSerializer
from .models import Cliente, Advogado, Processo, Tarefas
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import action, permission_classes
from django.http import JsonResponse
from django.conf import settings
from .emailSender import EmailSender
from django.shortcuts import get_object_or_404
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
    
    
class TarefasViewSet(viewsets.ModelViewSet):
    queryset = Tarefas.objects.all()
    serializer_class = TarefasSerializer
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
    sexo = data.get('sexo')
    email = data.get('email')
    password = data.get('password')
    oab = data.get('oab')
    
    if not nome or not email:
        return JsonResponse ({"error": "Nome e email são obrigatórios."}, status=400)
    
    advogado = Advogado.objects.create(
        nome=nome, 
        email=email,
        sexo = sexo,
        oab = oab,
        password=password
        )
    advogado.set_password(password)
    advogado.save()
    return JsonResponse({'message': 'advogado registrado com sucesso'}, status=201)    
"""BUG no Login,02/06/2023
Descrição: O login diz que não existe usuário cadastrado com esse email, 
preciso debugar mais calmamente.
RESOLVIDO em 03/06/2023
"""


@csrf_exempt
def emailRequestSenha(request):
   if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        user = Advogado.objects.filter(email=email).first()
        refresh = RefreshToken.for_user(user)
        refresh["purpose"] = "reset_password" 
        print(refresh)
        emailSender = EmailSender('empresadoth@gmail.com')
        emailSender.startserver()
        message =f'CLIQUE NO LINK PARA RESETAR SUA SENHA: http://127.0.0.1:8000/resetPassword/{refresh}'
        emailSender.sendMensage('Resetar Senha', message)
        return JsonResponse({'message': 'email enviado com sucesso'}, status=201)
   else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
    

@csrf_exempt
def resetPassword(request, token):
    if request.method == 'POST':
        data = json.loads(request.body)
        password = data.get('password')
        refresh = RefreshToken(token)
        advogado = refresh.payload['user_id']
        advogado = Advogado.objects.get(id=advogado)
        advogado.set_password(password)
        advogado.save()
        return JsonResponse({'message': 'senha resetada com sucesso'}, status=201)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)


@permission_classes([IsAuthenticated])
@csrf_exempt
def processosClientes(request,cliente_id):
    if request.method == 'GET':
        
        if not cliente_id:
            return JsonResponse({'error': 'ID do cliente obrigatório.'}, status=400)     
        try:
            cliente = get_object_or_404(Cliente, id=cliente_id)
        except:
            return JsonResponse({'error': 'Cliente nao encontrado.'}, status=404)
        processos = Processo.objects.filter(clienteId=cliente)
        serializer = ProcessoSerializer(processos, many=True)
        jsonFile = serializer.data
        advogadoResponsavelNome = get_object_or_404(Advogado, id=jsonFile[0]['advogadoResponsavelId'])
        if jsonFile:
            try:
                jsonFile[0]['advogadoResponsavelNome']= advogadoResponsavelNome.nome
                jsonFile[0]['clienteNome'] = cliente.nome
            except:
                jsonFile[0]['advogadoResponsavelNome']= 'Não encontrados'
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
        
#O erro era no cachê   


@permission_classes([IsAuthenticated])
@csrf_exempt
def tarefasProcesso(request,processo_id):
    if request.method == 'GET':
        if not processo_id:
            return JsonResponse({'error': 'ID do processo obrigatório.'}, status=400)     
        try:
            tarefas = Tarefas.objects.filter(processoOrigemId=processo_id)    
        except:
            return JsonResponse({'error': 'Processo não encontrado.'})
        
        serializer = TarefasSerializer(tarefas, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
        
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
    
@permission_classes([IsAuthenticated])
@csrf_exempt
def processosAdvogado(request,advogado_id):
    if request.method == 'GET':
        if not advogado_id:
            return JsonResponse({'error': 'ID do advogado é obrigatório.'})
        try:
            processo = Processo.objects.filter(advogadoResponsavelId=advogado_id)   
        except:
            return JsonResponse({'error': 'Advogado nao encontrado.'})
        serializer = ProcessoSerializer(processo, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error' : 'Método não permitido.'}, status=405)
    

@permission_classes([IsAuthenticated])
@csrf_exempt
def advogadosResumido(request):
    if request.method == 'GET':
        advogados = Advogado.objects.all()
        serializer = AdvogadoResumidoSerializer(advogados, many = True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error' : 'Método não permitido'},status = 404)
    
    

@permission_classes([IsAuthenticated])
@csrf_exempt
def processosResumido(request):
    if request.method == 'GET':
        processos = Processo.objects.all()
        serializer =ProcesssosResumidoSerializer(processos, many = True)   
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error' : 'Método não permitido'},status = 404)
    
    


