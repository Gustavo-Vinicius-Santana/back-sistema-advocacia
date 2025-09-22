from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from django.views.decorators.csrf import csrf_exempt
from .models import *
from rest_framework.decorators import action, permission_classes,api_view
from django.http import JsonResponse
from django.conf import settings
from .emailSender import EmailSender
from django.shortcuts import get_object_or_404
import json
import jwt
from rest_framework_simplejwt.views import TokenObtainPairView
from jwt.exceptions import InvalidTokenError
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta, datetime, time
from dateutil.relativedelta import relativedelta




class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    
class ClienteEsperaViewSet(viewsets.ModelViewSet):
    queryset = ClienteEspera.objects.all()
    serializer_class = ClienteEsperaSerializer
    permission_classes = [IsAuthenticated]
    

class ClienteSemContratoViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.filter(contrato=False)
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
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().order_by('-prioritario').filter(status = 'aberto')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    # com o class meta não funcionou, mas sobrescrevendo o list sim... ???
    # vou investigar o motivo
    
    
    
class TarefasViewSet(viewsets.ModelViewSet):
    queryset = Tarefas.objects.all()
    serializer_class = TarefasSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        hoje = timezone.localdate()
        data_limite = hoje + timedelta(days=3)
        limite = datetime.combine(data_limite, time.max)  # até 23:59:59

        # 1 - Atrasadas (somente antes de hoje)
        Tarefas.objects.filter(
            prazoFinal__lt=hoje
        ).exclude(status='concluida').update(status='atrasada')

        # 2 - Perto do prazo (inclui hoje até 3 dias depois)
        Tarefas.objects.filter(
            prazoFinal__gte=hoje,
            prazoFinal__lte=limite
        ).exclude(status='concluida').update(status='perto do prazo')

        # 3 - Em aberto (prazo maior que 3 dias)
        Tarefas.objects.filter(
            prazoFinal__gt=limite
        ).exclude(status='concluida').update(status='em aberto')

        return Tarefas.objects.filter(concluida=False).order_by('-urgente','prazoFinal') #urgente Primeiro, e prazoFinal depois
    def create(self, request, *args, **kwargs):
        hoje = timezone.localdate()
        data = request.data.copy()
        data['dataInicio'] = hoje
        prazoFinal_str = data.get('prazoFinal')
        if prazoFinal_str < hoje.strftime('%Y-%m-%d'):
            response = {
                'error': 'A data de prazoFinal nao pode ser anterior a data de hoje.'
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        dados_antes = self.get_serializer(instance).data.copy()  
        response = super().partial_update(request, *args, **kwargs)
        instance.refresh_from_db()  # Atualiza a instância do banco de dados
        dados_depois = self.get_serializer(instance).data.copy()
        campos_mudados = []
        #verificação do prazo final
        prazoFinal_str = dados_depois.get('prazoFinal')
        if prazoFinal_str < timezone.localdate().strftime('%Y-%m-%d'):
            response = {
                'error': 'A data de prazoFinal nao pode ser anterior a data de hoje.'
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        for campo, valor_antes in dados_antes.items():
            valor_depois = dados_depois.get(campo)
            if valor_depois != valor_antes:
                campos_mudados.append(campo)
        tarefa_id = instance
        data_Hora = datetime.now().strftime('%Y-%m-%d %H:%M')
        if request.user.is_authenticated:
            advogado_nome = Advogado.objects.get(id=request.user.id).nome
        if campos_mudados:
            # transforma lista em string: 'campo1','campo2','campo3'
            campos_mudados_formatados = ", ".join([f"'{campo}'" for campo in campos_mudados])
            historico = HistoricoTarefas.objects.create(
                tarefaId=tarefa_id,
                dataHora=data_Hora,
                acao=f'{data_Hora} - {advogado_nome} alterou o(s) campo(s): {campos_mudados_formatados}'
            )
            historico.save()
                
        

        return response


    
    
class DocumentosViewSet(viewsets.ModelViewSet):
    queryset = Documentos.objects.all()
    serializer_class = DocumentosSerializer
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
        


@permission_classes([IsAuthenticated])
@csrf_exempt
def processosArquivados(request):
    if request.method == 'GET':
        processos = Processo.objects.filter(status='arquivado')
        if processos is None:
            return JsonResponse({'error': 'Nenhum processo arquivado encontrado.'}, status=404)
        serializer = ProcessoSerializer(processos, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
   
   
@permission_classes([IsAuthenticated])
@csrf_exempt
def processosArquivadosEspecificos(request,processo_id):
    if request.method == 'GET':
        if not processo_id:
            return JsonResponse({'error': 'ID do processo é obrigatório.'},status=400)
        try:
            processo = Processo.objects.get(id=processo_id,status='arquivado')
        except Processo.DoesNotExist:
            return JsonResponse({'error': 'Processo não encontrado ou não arquivado.'},status=404)
        serializer = ProcessoSerializer(processo)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
    elif request.method == 'PUT':
        if not processo_id:
            return JsonResponse({'error': 'ID do processo é obrigatório.'},status=400)
        try:
            processo = Processo.objects.get(id=processo_id,status='arquivado')
        except Processo.DoesNotExist:
            return JsonResponse({'error': 'Processo não encontrado ou não arquivado.'},status=404)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Dados inválidos.'})
        serializer = ProcessoSerializer(processo, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=200)
        return JsonResponse(serializer.errors, status=400)
    
    elif request.method == 'PATCH':
        if not processo_id:
            return JsonResponse({'error': 'ID do processo é obrigatório.'},status=400)
        try:
            processo = Processo.objects.get(id=processo_id,status='arquivado')
        except Processo.DoesNotExist:
            return JsonResponse({'error': 'Processo não encontrado ou não arquivado.'},status=404)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Dados inválidos.'})
        serializer = ProcessoSerializer(processo, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=200)
        return JsonResponse(serializer.errors, status=400)
    
    elif request.method == 'DELETE':
        if not processo_id:
            return JsonResponse({'error': 'ID do processo é obrigatório.'},status=400)
        try:
            processo = Processo.objects.get(id=processo_id,status='arquivado')
        except Processo.DoesNotExist:
            return JsonResponse({'error': 'Processo nao encontrado ou nao arquivado.'},status=404)
        processo.delete()
        return JsonResponse({'message': 'Processo excluido com sucesso'}, status=201)
    else:
        return JsonResponse({'error' : 'Método não permitido.'},status = 405)   


@permission_classes([IsAuthenticated])
@csrf_exempt
def clientes65(request):
    if request.method == 'GET':
        dataAtual = timezone.now().date()

        # intervalo de nascimentos para quem fará 65 anos em até 5 dias
        dataInicio = dataAtual - relativedelta(years=65)               # completa 65 hoje
        dataFim = dataAtual - relativedelta(years=65, days=-5)         # completa 65 daqui 5 dias

        clientes = Cliente.objects.filter(dataNascimento__range=(dataInicio, dataFim))
        serializer = ClienteSerializer(clientes, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)



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
def tarefasConcluidasEspecificas(request,tarefa_id):
    if request.method == 'GET':
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)     
        try:
            tarefa = Tarefas.objects.get(id=tarefa_id,concluida = True)  
        except Tarefas.DoesNotExist:
            return JsonResponse({'error': 'Tarefa não encontrada ou não concluída.'}, status=404)
        
        serializer = TarefasSerializer(tarefa)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
    elif request.method == 'PUT':
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)     
        try:
            tarefa = Tarefas.objects.get(id=tarefa_id,concluida = True)  
        except Tarefas.DoesNotExist:
            return JsonResponse({'error': 'Tarefa não encontrada ou não concluída.'}, status=404)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Dados inválidos.'}, status=400)
        serializer = TarefasSerializer(tarefa, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=200)
        return JsonResponse(serializer.errors, status=400)
    
    elif request.method == 'DELETE':
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)     
        try:
            tarefa = Tarefas.objects.get(id=tarefa_id,concluida = True)  
        except Tarefas.DoesNotExist:
            return JsonResponse({'error': 'Tarefa não encontrada ou não concluída.'}, status=404)
        tarefa.delete()
        return JsonResponse({'message': 'Tarefa excluída com sucesso.'}, status=204)
    
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)


@permission_classes([IsAuthenticated])
@csrf_exempt
def historicoTarefasEspecificos(request,tarefa_id):
    if request.method == 'GET':
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)     
        try:
            historico = HistoricoTarefas.objects.filter(tarefaId=tarefa_id)  
        except HistoricoTarefas.DoesNotExist:
            return JsonResponse({'error': 'Histórico não encontrado.'}, status=404)
        
        serializer = HistoricoTarefasSerializer(historico, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
    elif request.method == 'DELETE':
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)     
        try:
            historico = HistoricoTarefas.objects.filter(tarefaId=tarefa_id)  
        except HistoricoTarefas.DoesNotExist:
            return JsonResponse({'error': 'Histórico não encontrado.'}, status=404)
        historico.delete()
        return JsonResponse({'message': 'Histórico excluído com sucesso.'}, status=204)
    
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
    
    
    
@permission_classes([IsAuthenticated])
@csrf_exempt
def historicoTarefas(request):
    if request.method == 'GET':
        historico = HistoricoTarefas.objects.all()
        serializer = HistoricoTarefasSerializer(historico, many=True)
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
def processosConcluidosEspecificos(request,processo_id):
    if request.method == 'GET':
        if not processo_id:
            return JsonResponse({'error': 'ID do processo é obrigatório.'},status=400)
        try:
            processo = Processo.objects.get(id=processo_id,concluido=True)
        except Processo.DoesNotExist:
            return JsonResponse({'error': 'Processo não encontrado ou não concluído.'},status=404)
        serializer = ProcessoSerializer(processo)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
    elif request.method == 'PUT':
        if not processo_id:
            return JsonResponse({'error': 'ID do processo é obrigatório.'},status=400)
        try:
            processo = Processo.objects.get(id=processo_id,concluido=True)
        except Processo.DoesNotExist:
            return JsonResponse({'error': 'Processo não encontrado ou não concluído.'},status=404)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Dados inválidos.'})
        serializer = ProcessoSerializer(processo, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=200)
        return JsonResponse(serializer.errors, status=400)
    
    elif request.method == 'PATCH':
        if not processo_id:
            return JsonResponse({'error': 'ID do processo é obrigatório.'},status=400)
        try:
            processo = Processo.objects.get(id=processo_id,concluido=True)
        except Processo.DoesNotExist:
            return JsonResponse({'error': 'Processo não encontrado ou não concluído.'},status=404)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Dados inválidos.'})
        serializer = ProcessoSerializer(processo, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=200)
        return JsonResponse(serializer.errors, status=400)
    else:
        return JsonResponse({'error' : 'Método não permitido.'},status = 405)
    

@permission_classes([IsAuthenticated])
@csrf_exempt
def tarefasAdvogadoCriador(request,advogado_id):
    if request.method == 'GET':
        if not advogado_id:
            return JsonResponse({'error': 'ID do advogado é obrigatório.'})
        try:
            tarefas = Tarefas.objects.filter(advogadoResponsavelId=advogado_id,concluida=False)   
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
        processosAtivos = Processo.objects.filter(advogadoCriadorId=advogado_id, status='ativo').exclude(concluido=True).count()
        
        if not tarefas.exists():
            return JsonResponse({'error': 'Nenhuma tarefa encontrada com esse advogado.'},status=400)
        
        tarefasConcluidas = tarefas.filter(concluida=True).count()
        tarefasPendentes = tarefas.filter(concluida=False).count()
        processosConcluidos = Processo.objects.filter(advogadoCriadorId=advogado_id, concluido=True).count()
        
        
        
        return JsonResponse({
            'tarefasConcluidas':tarefasConcluidas,
            'tarefasPendentes': tarefasPendentes,
            'processosAtivos': processosAtivos,
            'processosConcluidos': processosConcluidos,
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