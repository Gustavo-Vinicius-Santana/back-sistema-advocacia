from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import ClienteSerializer, AdvogadoSerializer, ProcessoSerializer,TarefasSerializer,AdvogadoResumidoSerializer,ProcesssosResumidoSerializer,CustomTokenObtainPairSerializer,ClienteEsperaSerializer
from .models import Cliente, Advogado, Processo, Tarefas,ClienteEspera
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import action, permission_classes,api_view
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q
from .emailSender import EmailSender
from django.shortcuts import get_object_or_404
import json
import jwt
from rest_framework_simplejwt.views import TokenObtainPairView
from jwt.exceptions import InvalidTokenError
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta




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
    def list(self, request, *args, **kwargs):
        hoje = timezone.localdate()
        limite  = hoje + timedelta(days=3)
       # Atualiza o status das tarefas com prazo final atrasado
        Tarefas.objects.filter(
           prazoFinal__lt=hoje).exclude(status='Concluida').update(status='Atrasada')
        # Atualiza o status das tarefas com prazo final perto do prazo
        Tarefas.objects.filter(
              prazoFinal__gte=hoje, prazoFinal__lte=limite, status='em aberto').exclude(status='concluida').update(status='Perto do Prazo'
        )       
        # Atualiza o status da tarefa caso o prazo final seja alterado
        Tarefas.objects.filter(
            Q(status='Atrasada') | Q(status='Perto do Prazo'),
            prazoFinal__gt=limite
        ).exclude(status='Concluida').update(status='Em Aberto')
        return super().list(request, *args, **kwargs) 
   
"""isso ta voltando um warning no meu console, pois estou misturando data naive(sem fuso)
com data com fuso, o warning não impede o funcionamento, mas é bom corrigir depois."""

class ClienteEsperaViewSet(viewsets.ModelViewSet):
    queryset = ClienteEspera.objects.all()
    serializer_class = ClienteEsperaSerializer
    permission_classes = [IsAuthenticated]
    
    
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

                    
                    
                    
class AdvogadosOnlineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        advogados = Advogado.objects.filter(is_online=True)
        serializer = AdvogadoSerializer(advogados, many=True)
        return Response(serializer.data)


class AdvogadoLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.is_online = False
        user.save()
        return Response({"detail": "Logout realizado com sucesso."})
        #implementar o logout baseado no tempo do Token JWT



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
    telefone = data.get('telefone')
    email = data.get('email')
    password = data.get('password')
    oab = data.get('oab')
    
    if not nome or not email:
        return JsonResponse ({"error": "Nome e email são obrigatórios."}, status=400)
    
    advogado = Advogado.objects.create(
        nome=nome, 
        telefone=telefone,
        email=email,
        oab = oab,
        password=password
        )
    advogado.set_password(password)
    advogado.save()
    return JsonResponse({'message': 'advogado registrado com sucesso'}, status=201)    
"""BUG no Login,02/06/2025
Descrição: O login diz que não existe usuário cadastrado com esse email, 
preciso debugar mais calmamente.
RESOLVIDO em 03/06/2025
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
        advogadCriadorNome = get_object_or_404(Advogado, id=jsonFile[0]['advogadoCriadorId'])
        if jsonFile:
            try:
                jsonFile[0]['advogadCriadorNome']= advogadCriadorNome.nome
                jsonFile[0]['clienteNome'] = cliente.nome
            except:
                jsonFile[0]['advogadCriadorNome']= 'Não encontrados'
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
    
    

@permission_classes([IsAuthenticated])
@csrf_exempt
def tarefasAdvogadoCriador(request,advogado_id):
    if request.method == 'GET':
        if not advogado_id:
            return JsonResponse({'error': 'ID do advogado é obrigatório.'})
        try:
            tarefas = Tarefas.objects.filter(advogadoResponsavelId=advogado_id)   
        except:
            return JsonResponse({'error': 'Advogado nao encontrado.'})
        if not tarefas:
            return JsonResponse({'error': 'Nenhuma tarefa encontrada com esse advogado.'})
        serializer = TarefasSerializer(tarefas, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error' : 'Método não permitido.'}, status=405)


@permission_classes([IsAuthenticated])
@csrf_exempt
def advogadosDashboard(request,advogado_id):
    if request.method == 'GET':
        if not advogado_id:
            return JsonResponse({'error': 'ID do advogado é obrigatório.'},status=400)
        tarefas = Tarefas.objects.filter(advogadoResponsavelId=advogado_id)
        processosCriados = Processo.objects.filter(advogadoCriadorId=advogado_id).count()
        
        if not tarefas.exists():
            return JsonResponse({'error': 'Nenhuma tarefa encontrada com esse advogado.'},status=400)
        
        tarefasConcluidas = tarefas.filter(status='concluida').count()
        tarefasPendentes = tarefas.filter(status='pendente').count()
        
        
        
        return JsonResponse({
            'tarefasConcluidas':tarefasConcluidas,
            'tarefasPendentes': tarefasPendentes,
            'processosCriados': processosCriados
        },safe=True)
    else:
        return JsonResponse({'error' : 'Método não permitido.'},status = 405) 
        
    
    

@permission_classes([IsAuthenticated])
@api_view(['GET'])
def advUserInfo(request):
    token = request.headers.get('Authorization')

    if not token:
        return Response({'error': 'Token não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token_format = token.split(' ')[1]
        payload = jwt.decode(token_format, settings.SECRET_KEY, algorithms=['HS256'])
        advogado_id = payload.get('user_id')
        advogado = Advogado.objects.get(id=advogado_id)
        serializer = AdvogadoSerializer(advogado)
        return Response(serializer.data)
    except IndexError:
        return Response({'error': 'Formato do token inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    except InvalidTokenError:
        return Response({'error': 'Token inválido ou expirado.'}, status=status.HTTP_401_UNAUTHORIZED)
    except Advogado.DoesNotExist:
        return Response({'error': 'Advogado não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@permission_classes([IsAuthenticated])
@csrf_exempt
def clientesEsperaAdv(request,advogado_id):
    if request.method == 'GET':
        if not advogado_id:
            return JsonResponse({'error':'O ID do advogado é obrigatório.'})
        try:
            clientesEsperaAdv = []
            clientesEspera = ClienteEspera.objects.filter(IdAdvogado=advogado_id)
            for cliente in clientesEspera:
                cliente_data = {
                    'id': cliente.id,
                    'nome': cliente.nome,
                    'telefone': cliente.telefone,
                    'observacao': cliente.observacao,
                    'IdAdvogado': cliente.IdAdvogado,
                    'cpf': cliente.cpf
                }
                clientesEsperaAdv.append(cliente_data)
            return JsonResponse(clientesEsperaAdv, safe=False)
        except ClienteEspera.DoesNotExist:
            return JsonResponse({'error': 'Nenhum cliente encontrado.'}, status=404)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)        