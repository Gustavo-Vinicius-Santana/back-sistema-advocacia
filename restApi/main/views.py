from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from django.views.decorators.csrf import csrf_exempt
from .models import *
from rest_framework.decorators import action, permission_classes,api_view
from django.http import JsonResponse
from django.conf import settings
from .emailSender import EmailSender
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, Value, IntegerField
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
    
    def list(self, request, *args, **kwargs):
        dataAtual = timezone.now().date()

        # Intervalo para quem está dentro de ±5 dias de completar 65 anos
        data65 = dataAtual - relativedelta(years=65)
        dataInicio = data65 - relativedelta(days=5)  # já fez (até 5 dias atrás)
        dataFim = data65 + relativedelta(days=5)     # vai fazer (até 5 dias à frente)

        queryset = self.get_queryset().filter(contrato=True).annotate(
            prioridade=Case(
                When(
                    dataNascimento__range=(dataInicio, dataFim),
                    then=Value(1)
                ),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-prioridade', 'id')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RepresentanteViewSet(viewsets.ModelViewSet):
    queryset = Representante.objects.all()
    serializer_class = RepresentanteSerializer
    permission_classes = [IsAuthenticated]
    
class ClienteEsperaViewSet(viewsets.ModelViewSet):
    queryset = ClienteEspera.objects.all()
    serializer_class = ClienteEsperaSerializer
    permission_classes = [IsAuthenticated]
  
  
class ParceirosViewSet(viewsets.ModelViewSet):
    queryset = Parceiros.objects.all()
    serializer_class = ParceirosSerializer
    permission_classes = [IsAuthenticated]
    

class EscritoriosViewSet(viewsets.ModelViewSet):
    queryset = Escritorios.objects.all()
    serializer_class = EscritoriosSerializer
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
        queryset = self.get_queryset().order_by('-prioritario').filter(status = 'ativo')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    # com o class meta não funcionou, mas sobrescrevendo o list sim... ???
    # vou investigar o motivo
    
class GrupoAcaoViewSet(viewsets.ModelViewSet):
    queryset = GrupoAcao.objects.all()
    serializer_class = GrupoAcaoSerializer
    permission_classes = [IsAuthenticated]  


class TipoAcaoViewSet(viewsets.ModelViewSet):
    queryset = TipoAcao.objects.all()
    serializer_class = TipoAcaoSerializer
    permission_classes = [IsAuthenticated]
    
    
class FaseProcessoViewSet(viewsets.ModelViewSet):
    queryset = FaseProcesso.objects.all()
    serializer_class = FaseProcessoSerializer
    permission_classes = [IsAuthenticated]
    
    
class EtapaProcessoViewSet(viewsets.ModelViewSet):
    queryset = EtapaProcesso.objects.all()
    serializer_class = EtapaProcessoSerializer
    permission_classes = [IsAuthenticated]
    
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

        return Tarefas.objects.filter(concluida=False,deletada=False).order_by('-urgente','prazoFinal') #urgente Primeiro, e prazoFinal depois
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
        tiposLista = TipoTarefa.objects.all() 
        tipos = []
        for e in tiposLista:
            tipos.append(e.nome)
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'error': str(e),'tipos disponíveis':tipos}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        token = request.headers.get('Authorization')

        if not token:
            return Response({'error': 'Token não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_format = token.split(' ')[1]
        except IndexError:
            return Response({'error': 'Token inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        payload = jwt.decode(token_format, settings.SECRET_KEY, algorithms=['HS256'])
        advogado_id = payload.get('user_id')
        advogado = Advogado.objects.get(id=advogado_id)
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
                if campo == 'deletada':
                    if valor_depois == True:
                        instance.deletadaPor = advogado.nome
                        instance.save()
                
        tarefa_id = instance
        data_Hora = datetime.now().strftime('%Y-%m-%d %H:%M')
        if request.user.is_authenticated:
            advogado_nome = advogado.nome
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
    

class TipoTarefaViewSet(viewsets.ModelViewSet):
    queryset = TipoTarefa.objects.all()
    serializer_class = TipoTarefaSerializer
    permission_classes= [IsAdminUser]


    
    
class DocumentosViewSet(viewsets.ModelViewSet):
    queryset = Documentos.objects.all()
    serializer_class = DocumentosSerializer
    permission_classes = [IsAuthenticated]    
    
    
class ArquivoModelViewSet(viewsets.ModelViewSet):
    queryset = ArquivoModel.objects.all()
    serializer_class = ArquivoModelSerializer
    permission_classes = [IsAuthenticated]

    
class ArquivoTarefaViewSet(viewsets.ModelViewSet):
    queryset = ArquivoTarefa.objects.all()
    serializer_class = ArquivoTarefaSerializer
    permission_classes = [IsAuthenticated]
    
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

                    
class ArquivoModelClienteIdView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, cliente):
        try:
            arquivos = ArquivoModel.objects.filter(cliente_id=cliente)
        except ArquivoModel.DoesNotExist:
            return Response({'error': 'ArquivoModel nao encontrado.'}, status=404)
        serializer = ArquivoModelSerializer(arquivos, many=True)
        return Response(serializer.data)  

class ArquivoTarefaIdView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, tarefa):
        try:
            arquivos = ArquivoTarefa.objects.filter(tarefa_id=tarefa)
        except ArquivoTarefa.DoesNotExist:
            return Response({'error': 'ArquivoModel nao encontrado.'}, status=404)
        serializer = ArquivoTarefaSerializer(arquivos, many=True)
        return Response(serializer.data)  

                    
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
    foto = data.get('foto')  # ✅ novo campo

    if not nome or not email:
        return JsonResponse({"error": "Nome e email são obrigatórios."}, status=400)

    advogado = Advogado.objects.create(
        nome=nome, 
        telefone=telefone,
        email=email,
        oab=oab,
        foto=foto  # ✅ salva a URL da foto
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
        emailSender = EmailSender(email)
        emailSender.startserver()
        message =f'CLIQUE NO LINK PARA RESETAR SUA SENHA: http://127.0.0.1:3000/recovery/newPassword/{refresh}'
        emailSender.sendMensage('Resetar Senha', message)
        return JsonResponse({'message': 'email enviado com sucesso'}, status=201)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
    
def get_id_from_token(token):
    token_format = token.split(' ')[1]
    payload = jwt.decode(token_format, settings.SECRET_KEY, algorithms=['HS256'])
    return payload.get('user_id')
    
def validate_reset_token(token):
    try:
        refresh = RefreshToken(token)
        if refresh.payload.get("purpose") != "reset_password":
            return False
        return True
    except InvalidTokenError:
        return False

        
def validate_reset_token_endpoint(request,token):
    try:
        refresh = RefreshToken(token)
        if refresh.payload.get("purpose") != "reset_password":
            return JsonResponse({'valid': False}, status=200)
        return JsonResponse({'valid': True}, status=200)
    except InvalidTokenError:
        return JsonResponse({'valid': False}, status=200)
    

@csrf_exempt
def resetPassword(request, token):
    if request.method == 'POST':
        data = json.loads(request.body)
        password = data.get('password')
        if not validate_reset_token(token):
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


#Apagar se realmente não for usar, comentada em 17/10/2025
#Assim como o seu respectivo trecho em main/urls.py
"""
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
"""


@permission_classes([IsAuthenticated])
@csrf_exempt
def clientesSemContrato(request):
    if request.method == 'GET':
        dataAtual = timezone.now().date()

        # intervalo de nascimentos para quem fará 65 anos em até 5 dias
        data65 = dataAtual - relativedelta(years=65)
        dataInicio = data65 - relativedelta(days=5)  # já fez (até 5 dias atrás)
        dataFim = data65 + relativedelta(days=5) 

        clientes = Cliente.objects.filter(contrato = False).annotate(
            prioridade=Case(
                When(
                    dataNascimento__range=(dataInicio, dataFim),
                    then=Value(1)
                ),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-prioridade','id')
   
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
            tarefas = Tarefas.objects.filter(processoOrigemId=processo_id,deletada=False)  
        except:
            return JsonResponse({'error': 'Processo não encontrado.'})
        
        serializer = TarefasSerializer(tarefas, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
        
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
        


# editador por dennis
@permission_classes([IsAuthenticated])
@csrf_exempt
def tarefasDeletadas(request):
    if request.method == 'GET':
        tarefas = Tarefas.objects.filter(deletada=True)
        try:
            tarefas = Tarefas.objects.filter(deletada=True)
        except:
            return JsonResponse({'error': 'Nenhuma tarefa deletada encontrada.'}, status=404)
        serializer = TarefasSerializer(tarefas, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)





@permission_classes([IsAuthenticated])
@csrf_exempt
def tarefasDeletadasEspecificas(request,tarefa_id):
    if request.method == 'GET':
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)     
        try:
            tarefa = Tarefas.objects.get(id=tarefa_id,deletada = True)  
        except Tarefas.DoesNotExist:
            return JsonResponse({'error': 'Tarefa não encontrada ou nao deletada.'}, status=404)
        
        serializer = TarefasSerializer(tarefa)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    elif request.method == 'PATCH':
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)     
        try:
            tarefa = Tarefas.objects.get(id=tarefa_id,deletada = True)  
        except Tarefas.DoesNotExist:
            return JsonResponse({'error': 'Tarefa não encontrada ou nao deletada.'}, status=404)
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
            return JsonResponse({'error':'Tarefa não encontrada ou nao deletada.'}, status=400)
        try: 
            tarefas = Tarefas.objects.get(id=tarefa_id,deletada = True)
        except Tarefas.DoesNotExist:
            return JsonResponse({'error': 'Tarefa não encontrada ou nao deletada.'}, status=404)
        tarefas.delete()
        return JsonResponse({'message': 'Tarefa excluida com sucesso.'}, status=200)
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
        return JsonResponse({'message': 'Tarefa excluida com sucesso.'}, status=204)
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
    
        try:
            historico = HistoricoTarefas.objects.all()  
        except HistoricoTarefas.DoesNotExist:
            return JsonResponse({'error': 'Histórico não encontrado.'}, status=404)
    
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
            tarefas = Tarefas.objects.filter(advogadoResponsavelId=advogado_id,concluida=False,deletada = False)   
        except:
            return JsonResponse({'error': 'Advogado nao encontrado.'})
        if not tarefas:
            return JsonResponse({'error': 'Nenhuma tarefa encontrada com esse advogado.'})
        tarefasOrdenadas = tarefas.order_by('-urgente','prazoFinal')
        serializer = TarefasSerializer(tarefasOrdenadas, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error' : 'Método não permitido.'}, status=405)


# editado por dennis
@permission_classes([IsAuthenticated])
@csrf_exempt
def advogadosDashboard(request,advogado_id):
    if request.method == 'GET':
        if not advogado_id:
            return JsonResponse({'error': 'ID do advogado é obrigatório.'},status=400)
        try:
            advogado = Advogado.objects.get(id=advogado_id)
        except Advogado.DoesNotExist:
            return JsonResponse({'error': 'Advogado nao encontrado.'},status=404)
        try:
            tarefas = Tarefas.objects.filter(advogadoResponsavelId=advogado_id)
        except:
            return JsonResponse({'error': 'Advogado nao encontrado.'},status=404)
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
                    'observacoes': cliente.observacoes,
                    'IdAdvogado': cliente.IdAdvogado,
                    'cpf': cliente.cpf,
                    'dataNascimento':cliente.dataNascimento
                }
                clientesEsperaAdv.append(cliente_data)
            return JsonResponse(clientesEsperaAdv, safe=False)
        except ClienteEspera.DoesNotExist:
            return JsonResponse({'error': 'Nenhum cliente encontrado.'}, status=404)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)        



# Conjunto de funções para métricas dos gráficos
@csrf_exempt
@permission_classes([IsAuthenticated])
def graficoProcessosTipo(request):
    if request.method == 'GET':
        processosRuins = Processo.objects.filter(classificacao = 'ruim').count()
        processosBons = Processo.objects.filter(classificacao = 'bom').count()
        jsonFile = [
            {"classificacao":"ruim",
            "quantidade":processosRuins,
            },
            {"classificacao":"bom",
            "quantidade":processosBons,
            }
        ]
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)


@csrf_exempt
@permission_classes([IsAuthenticated])
def graficoProcessosGrupo(request):
    if request.method == 'GET':
        processosPrevidenciario = Processo.objects.filter(grupoAcao = 'previdenciario').count()
        processoTrabalhista = Processo.objects.filter(grupoAcao = 'trabalhista').count()
        jsonFile = [
            {
            "grupo":"previdenciario",
            "quantidade":processosPrevidenciario,               
            },
            {
            "grupo":"trabalhista",
            "quantidade":processoTrabalhista,
            }
        ]
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

        
@csrf_exempt
@permission_classes([IsAuthenticated])        
def graficoProcessosStatus(request):
    if request.method == 'GET':
        processosStatusAtivo = Processo.objects.filter(status = 'ativo').count()
        processoStatusArquivados = Processo.objects.filter(status = 'arquivado').count()
        jsonFile = [
            {
            "status":"ativo",
            "quantidade":processosStatusAtivo,               
            },
            {
            "status":"arquivados",
            "quantidade":processoStatusArquivados,
            }
        ]
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

        
@csrf_exempt
@permission_classes([IsAuthenticated])
def graficoClientesContrato(request):
    if request.method == 'GET':
        clientesComContrato = Cliente.objects.filter(contrato = True).count()
        clientesSemContrato = Cliente.objects.filter(contrato = False).count()
        jsonFile = [
            {
            "contrato":"com contrato",
            "quantidade":clientesComContrato,               
            },
            {
            "contrato":"sem contrato",
            "quantidade":clientesSemContrato,
            }
        ]
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

        
@csrf_exempt
@permission_classes([IsAuthenticated])
def graficoClientesParceiro(request):
    if request.method == 'GET':
        parceiros = Parceiros.objects.all()
        jsonFile = []
        for parceiro in parceiros:
            count = Cliente.objects.filter(parceiro=parceiro.nome).count()
            jsonFile.append({
                "parceiro": parceiro.nome,
                "quantidade": count
            })
        
        #pegar os clientes com de cada parceiro
        #agrupa pelos parceiros
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

        
# editado por dennis
@csrf_exempt
@permission_classes([IsAuthenticated])
def graficoTarefasStatus(request):
    if request.method == 'GET':
        try:
            tarefasConcluidas = Tarefas.objects.filter(concluida = True).count()
        except:
            tarefasConcluidas = 0
        try:
            tarefasEmAberto = Tarefas.objects.filter(concluida = False).count()
        except:
            tarefasEmAberto = 0
        jsonFile = [
            {
            "status":"concluidas",
            "quantidade":tarefasConcluidas,               
            },
            {
            "status":"em aberto",
            "quantidade":tarefasEmAberto,
            }
        ]
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
    
# editado por dennis
@csrf_exempt
@permission_classes([IsAuthenticated])
def graficoTarefasAdvogado(request):
    if request.method == 'GET':
        try:
            advogados = Advogado.objects.all()
        except:
            return JsonResponse({'error': 'Nenhum advogado encontrado.'}, status=404)
        
        jsonFile = []
        for advogado in advogados:
            count = Tarefas.objects.filter(advogadoResponsavelId=advogado.id,deletada=False).count()
            jsonFile.append({
                "advogado": advogado.nome,
                "quantidade": count
            })
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
    
# editado por dennis    
@csrf_exempt
@permission_classes([IsAuthenticated])
def etapasPorFase(request,fase_id):
    if request.method == 'GET':
        try:
            etapas = EtapaProcesso.objects.filter(faseProcesso=fase_id)
        except EtapaProcesso.DoesNotExist:
            return JsonResponse({'error': 'Etapas nao encontradas.'}, status=404)
        
        serializer = EtapaProcessoSerializer(etapas, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)


# editado por dennis
@csrf_exempt
@permission_classes([IsAuthenticated])
def tipoPorGrupo(request,grupo_id):
    if request.method == 'GET':
        try:
            tipo = TipoAcao.objects.filter(grupoAcao=grupo_id)
        except TipoAcao.DoesNotExist:
            return JsonResponse({'error': 'Tipo nao encontrado.'}, status=404)
        serializer = TipoAcaoSerializer(tipo, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)