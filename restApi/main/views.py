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
from django.db.models import Case, When, Value, IntegerField, Count, Q
import json
import jwt
from rest_framework_simplejwt.views import TokenObtainPairView
from jwt.exceptions import InvalidTokenError
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta, date, time
from dateutil.relativedelta import relativedelta
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.exceptions import ValidationError
from django.db.models.functions import ExtractDay, Now
from django.db.models import ExpressionWrapper, F, IntegerField
# Remova DurationField se não estiver usando
from django.db.models import DateField
import re




class standardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = standardResultsSetPagination
    
    def list(self, request, *args, **kwargs):
        dataAtual = timezone.now().date()

        # Intervalo para quem está dentro de ±5 dias de completar 65 anos
        data65 = dataAtual - relativedelta(years=65)
        dataInicio = data65 - relativedelta(days=5)
        dataFim = data65 + relativedelta(days=5)

        # Adicione as anotações para contar processos por categoria
        queryset = self.get_queryset().annotate(
            prioridade=Case(
                When(
                    dataNascimento__range=(dataInicio, dataFim),
                    then=Value(1)
                ),
                default=Value(0),
                output_field=IntegerField()
            ),
            # Total de processos ativos
            processos_ativos_count=Count(
                'processo',
                filter=Q(processo__status='ativo')
            ),
            # Total de processos arquivados
            processos_arquivados_count=Count(
                'processo',
                filter=Q(processo__status='arquivado')
            ),
            # Total de processos urgentes (ativos e prioritários)
            processos_urgentes_count=Count(
                'processo',
                filter=Q(processo__status='ativo') & 
                       Q(processo__prioritario=True)
            ),
            # Total geral de processos (todas as categorias)
            processos_total_count=Count('processo')
        ).order_by('-prioridade', 'id')
        
        # Filtro por contrato (novo parâmetro)
        contrato_param = request.query_params.get('contrato')
        if contrato_param is not None:
            if contrato_param.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(contrato=True)
            elif contrato_param.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(contrato=False)
            else:
                return Response({"error": "Valor inválido para o parâmetro 'contrato'. Use 'true' ou 'false'."}, status=400)
        
        # Parâmetros de filtro e ordenação
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')

        allowed_fields = [
            'nome','cpf','telefone','inss','parceiro'
        ]
        
        if field and value:
            if field not in allowed_fields:
                return Response({"error": "Campo de filtro inválido."}, status=400)

            # Campos simples
            if field in ['nome', 'cpf', 'telefone', 'inss']:
                queryset = queryset.filter(**{f"{field}__icontains": value})

            # Campo composto (parceiro)
            elif field == 'parceiro':
                queryset = queryset.filter(parceiro__nome__icontains=value)
        
        if order_by:
            if order_by == 'parceiro':
                queryset = queryset.order_by('parceiro__nome')
            else:
                queryset = queryset.order_by(order_by)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            
            # Calcular dias para 65 anos manualmente para cada cliente
            for item in response.data['results']:
                if item.get('dataNascimento'):
                    # Parse da data de nascimento
                    data_nasc_str = item['dataNascimento']
                    # Pode vir em diferentes formatos dependendo do serializer
                    if isinstance(data_nasc_str, str):
                        data_nasc = datetime.strptime(data_nasc_str, '%Y-%m-%d').date()
                    else:
                        # Se já for um objeto date
                        data_nasc = data_nasc_str
                    
                    # Calcular data de 65 anos
                    data_65 = data_nasc + relativedelta(years=65)
                    
                    # Calcular dias restantes
                    dias_para_65 = (data_65 - dataAtual).days
                    item['dias_para_65'] = dias_para_65
                else:
                    item['dias_para_65'] = None
            return response

        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        
        # Calcular dias para 65 anos para resposta sem paginação
        for item in data:
            if item.get('dataNascimento'):
                data_nasc_str = item['dataNascimento']
                if isinstance(data_nasc_str, str):
                    data_nasc = datetime.strptime(data_nasc_str, '%Y-%m-%d').date()
                else:
                    data_nasc = data_nasc_str
                
                data_65 = data_nasc + relativedelta(years=65)
                dias_para_65 = (data_65 - dataAtual).days
                item['dias_para_65'] = dias_para_65
            else:
                item['dias_para_65'] = None
                
        return Response(data)


class RepresentanteViewSet(viewsets.ModelViewSet):
    queryset = Representante.objects.all()
    serializer_class = RepresentanteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = standardResultsSetPagination  # Adiciona paginação aqui
    
    def get_queryset(self):
        # Queryset base - pode adicionar annotate se necessário
        queryset = Representante.objects.all()
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Parâmetros de filtro e ordenação
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')

        # Campos permitidos para busca
        allowed_fields = ['nome', 'cpf', 'telefone', 'email', 'cliente']
        
        # Queryset base
        queryset = self.get_queryset()
        
        # Filtro por campo e valor
        if field and value:
            if field not in allowed_fields:
                return Response({"error": "Campo de filtro inválido."}, status=400)

            # Filtro especial para cliente (relacionamento)
            if field == 'cliente':
                queryset = queryset.filter(cliente__nome__icontains=value)
            else:
                # Campos simples diretos no modelo
                if field in ['nome', 'cpf', 'telefone', 'email']:
                    queryset = queryset.filter(**{f"{field}__icontains": value})
        
        # Ordenação
        if order_by:
            # Permite ordenar pelos campos
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('id')
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Sem paginação
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    
class ClienteEsperaViewSet(viewsets.ModelViewSet):
    queryset = ClienteEspera.objects.all()
    serializer_class = ClienteEsperaSerializer
    permission_classes = [IsAuthenticated]
    

  
class ParceirosViewSet(viewsets.ModelViewSet):
    queryset = Parceiros.objects.all()
    serializer_class = ParceirosSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = standardResultsSetPagination
    
    def get_queryset(self):
        # Annota o queryset base com a contagem de clientes
        queryset = Parceiros.objects.annotate(
            total_clientes=Count('clientes')
        )
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Parâmetros de filtro e ordenação
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')

        # Campos permitidos para busca
        allowed_fields = ['nome', 'email', 'cpf', 'telefone']
        
        # Queryset base com annotate
        queryset = self.get_queryset()
        
        # Filtro por campo e valor
        if field and value:
            if field not in allowed_fields:
                return Response({"error": "Campo de filtro inválido."}, status=400)

            # Campos simples (todos os campos são diretos no modelo Parceiros)
            if field in ['nome', 'email', 'cpf', 'telefone']:
                queryset = queryset.filter(**{f"{field}__icontains": value})
        
        # Ordenação
        if order_by:
            # Permite ordenar por total_clientes também
            if order_by in ['total_clientes', '-total_clientes']:
                queryset = queryset.order_by(order_by)
            else:
                queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('id')
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Sem paginação
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    

class EscritoriosViewSet(viewsets.ModelViewSet):
    queryset = Escritorios.objects.all()
    serializer_class = EscritoriosSerializer
    permission_classes = [IsAuthenticated]
    
    # Adicione este atributo - assumindo que standardResultsSetPagination já está definido
    pagination_class = standardResultsSetPagination




    
class AdvogadoViewSet(viewsets.ModelViewSet):
    queryset = Advogado.objects.all()
    serializer_class = AdvogadoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = standardResultsSetPagination  # Adiciona a paginação aqui
    
    def get_queryset(self):
        """
        Annota o queryset base com as contagens de tarefas.
        """
        queryset = Advogado.objects.annotate(
            tarefas_criadas=Count(
                'advogadoCriador__id',
                distinct=True,
                filter=Q(advogadoCriador__deletada=False)
            ),
            tarefas_responsavel=Count(
                'advogadoResponsavel__id',
                distinct=True,
                filter=Q(advogadoResponsavel__deletada=False)
            )
        )
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Parâmetros de filtro e ordenação
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')

        # Campos permitidos para busca
        allowed_fields = ['nome', 'email', 'telefone', 'oab']
        
        # Queryset base com annotate
        queryset = self.get_queryset()
        
        # Filtro por campo e valor
        if field and value:
            if field not in allowed_fields:
                return Response({"error": "Campo de filtro inválido."}, status=400)

            # Campos simples
            if field in ['nome', 'email', 'telefone', 'oab']:
                queryset = queryset.filter(**{f"{field}__icontains": value})
        
        # Ordenação
        if order_by:
            # Permite ordenar pelos campos annotados também
            annotate_fields = [
                'tarefas_criadas', '-tarefas_criadas',
                'tarefas_responsavel', '-tarefas_responsavel'
            ]
            
            if order_by in annotate_fields:
                queryset = queryset.order_by(order_by)
            else:
                queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('id')
        
        # Paginação - EXATAMENTE IGUAL À VIEW DE PARCEIROS
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Sem paginação
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ProcessoViewSet(viewsets.ModelViewSet):
    queryset = Processo.objects.all()
    serializer_class = ProcessoSerializer  # Seu serializer original
    permission_classes = [IsAuthenticated]
    pagination_class = standardResultsSetPagination
    
    def get_queryset(self):
        """
        Annota o queryset com as contagens de tarefas.
        Como o serializer usa fields='__all__', os campos annotate serão incluídos.
        """
        queryset = Processo.objects.annotate(
            total_tarefas=Count('tarefas', filter=Q(tarefas__deletada=False)),
            tarefas_em_aberto=Count(
                'tarefas',
                filter=Q(tarefas__deletada=False, tarefas__concluida=False, tarefas__status='em aberto')
            ),
            tarefas_atrasadas=Count(
                'tarefas',
                filter=Q(tarefas__deletada=False, tarefas__concluida=False, tarefas__status='atrasada')
            ),
            tarefas_concluidas=Count(
                'tarefas',
                filter=Q(tarefas__deletada=False, tarefas__concluida=True)
            ),
            tarefas_urgentes=Count(
                'tarefas',
                filter=Q(tarefas__deletada=False, tarefas__urgente=True, tarefas__concluida=False)
            ),
            tarefas_perto_prazo=Count(
                'tarefas',
                filter=Q(tarefas__deletada=False, tarefas__concluida=False, tarefas__status='perto do prazo')
            )
        )
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Começa com todos os processos (sem filtro padrão)
        queryset = self.get_queryset()

        # Parâmetros de filtro
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')
        
        # Filtro por status (se não especificar, mostra todos)
        status_filter = request.query_params.get('status')
        
        # Filtro por concluído (true/false) - novo parâmetro
        concluido_filter = request.query_params.get('concluido')
        
        # Filtros por data
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        periodo = request.query_params.get('periodo')  # Ex: 'hoje', 'semana', 'mes', 'ano'
        
        # NOVO: Filtro por ID do cliente
        cliente_id_filter = request.query_params.get('cliente_id')

        # Adicione os novos campos de tarefas aos campos permitidos
        allowed_fields = [
            'numeroProcesso',
            'fase',
            'status',
            'clienteId',
            'advogadoCriadorId',
            'dataContrato',
            'titulo',
            'classificacao',
            'prioritario',
            'concluido',
            # Novos campos de tarefas
            'total_tarefas',
            'tarefas_em_aberto',
            'tarefas_atrasadas',
            'tarefas_concluidas',
            'tarefas_urgentes',
            'tarefas_perto_prazo'
        ]

        # ---------------- NOVO: FILTRO POR ID DO CLIENTE ----------------
        if cliente_id_filter:
            try:
                cliente_id = int(cliente_id_filter)
                queryset = queryset.filter(clienteId__id=cliente_id)
            except (ValueError, TypeError):
                return Response({"error": "ID do cliente deve ser um número inteiro válido"}, status=400)

        # ---------------- FILTRO POR STATUS ----------------
        if status_filter:
            # Permite filtrar por um status específico ou por múltiplos status separados por vírgula
            status_list = [s.strip() for s in status_filter.split(',')]
            valid_statuses = ['ativo', 'arquivado']
            
            # Filtra apenas status válidos
            filtered_statuses = [s for s in status_list if s in valid_statuses]
            
            if filtered_statuses:
                if len(filtered_statuses) == 1:
                    queryset = queryset.filter(status=filtered_statuses[0])
                else:
                    queryset = queryset.filter(status__in=filtered_statuses)
            else:
                return Response({"error": "Status inválido. Use: 'ativo', 'arquivado' ou 'ativo,arquivado'"}, status=400)

        # ---------------- FILTRO POR CONCLUÍDO (PARÂMETRO SEPARADO) ----------------
        if concluido_filter is not None:
            if concluido_filter.lower() in ['true', '1', 'yes', 'sim', 'verdadeiro']:
                queryset = queryset.filter(concluido=True)
            elif concluido_filter.lower() in ['false', '0', 'no', 'não', 'nao', 'falso']:
                queryset = queryset.filter(concluido=False)
            else:
                return Response({"error": "Valor inválido para 'concluido'. Use: 'true' para concluídos ou 'false' para não concluídos"}, status=400)

        # ---------------- FILTRO POR CAMPOS ESPECÍFICOS ----------------
        if field and value:
            if field not in allowed_fields:
                return Response({"error": "Campo de filtro inválido."}, status=400)

            if field in ['numeroProcesso', 'fase', 'status', 'titulo', 'classificacao']:
                queryset = queryset.filter(**{f"{field}__icontains": value})

            elif field == 'clienteId':
                queryset = queryset.filter(clienteId__nome__icontains=value)

            elif field == 'advogadoCriadorId':
                queryset = queryset.filter(advogadoCriadorId__nome__icontains=value)
                
            elif field == 'dataContrato':
                # Filtro por data específica
                try:
                    # Precisa de teste posteriormente
                    data_valor = datetime(value) or date(value)
                    if data_valor:
                        data_inicio_dia = timezone.make_aware(datetime.combine(data_valor, datetime.min.time()))
                        data_fim_dia = timezone.make_aware(datetime.combine(data_valor, datetime.max.time()))
                        queryset = queryset.filter(dataContrato__range=[data_inicio_dia, data_fim_dia])
                except (ValueError, TypeError):
                    return Response({"error": "Formato de data inválido. Use YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS"}, status=400)
            
            elif field == 'prioritario':
                # Filtro por prioritário (true/false)
                if value.lower() in ['true', '1', 'yes', 'sim']:
                    queryset = queryset.filter(prioritario=True)
                elif value.lower() in ['false', '0', 'no', 'não']:
                    queryset = queryset.filter(prioritario=False)
                else:
                    return Response({"error": "Valor inválido para 'prioritario'. Use: 'true' ou 'false'"}, status=400)
            
            elif field == 'concluido':
                # Filtro por concluído (true/false) - ainda mantido para compatibilidade
                if value.lower() in ['true', '1', 'yes', 'sim']:
                    queryset = queryset.filter(concluido=True)
                elif value.lower() in ['false', '0', 'no', 'não']:
                    queryset = queryset.filter(concluido=False)
                else:
                    return Response({"error": "Valor inválido para 'concluido'. Use: 'true' ou 'false'"}, status=400)
            
            # --- NOVOS FILTROS PARA CAMPOS DE TAREFAS ---
            elif field == 'total_tarefas':
                try:
                    valor = int(value)
                    queryset = queryset.filter(total_tarefas=valor)
                except (ValueError, TypeError):
                    return Response({"error": "total_tarefas deve ser um número inteiro válido"}, status=400)
            
            elif field in ['tarefas_em_aberto', 'tarefas_atrasadas', 'tarefas_concluidas', 'tarefas_urgentes', 'tarefas_perto_prazo']:
                try:
                    valor = int(value)
                    if valor > 0:
                        queryset = queryset.filter(**{f"{field}__gte": valor})
                    else:
                        queryset = queryset.filter(**{field: 0})
                except (ValueError, TypeError):
                    return Response({"error": f"{field} deve ser um número inteiro válido"}, status=400)

        # ---------------- FILTRO POR PERÍODO DE DATA ----------------
        if data_inicio or data_fim or periodo:
            # Filtro por período específico (hoje, semana, mês, ano)
            if periodo:
                hoje = timezone.now().date()
                
                if periodo == 'hoje':
                    data_inicio_periodo = timezone.make_aware(datetime.combine(hoje, datetime.min.time()))
                    data_fim_periodo = timezone.make_aware(datetime.combine(hoje, datetime.max.time()))
                    queryset = queryset.filter(dataContrato__range=[data_inicio_periodo, data_fim_periodo])
                    
                elif periodo == 'semana':
                    inicio_semana = hoje - timedelta(days=hoje.weekday())  # Segunda-feira
                    fim_semana = inicio_semana + timedelta(days=6)  # Domingo
                    data_inicio_periodo = timezone.make_aware(datetime.combine(inicio_semana, datetime.min.time()))
                    data_fim_periodo = timezone.make_aware(datetime.combine(fim_semana, datetime.max.time()))
                    queryset = queryset.filter(dataContrato__range=[data_inicio_periodo, data_fim_periodo])
                    
                elif periodo == 'mes':
                    data_inicio_periodo = timezone.make_aware(datetime(hoje.year, hoje.month, 1, 0, 0, 0))
                    if hoje.month == 12:
                        data_fim_periodo = timezone.make_aware(datetime(hoje.year + 1, 1, 1, 0, 0, 0)) - timedelta(seconds=1)
                    else:
                        data_fim_periodo = timezone.make_aware(datetime(hoje.year, hoje.month + 1, 1, 0, 0, 0)) - timedelta(seconds=1)
                    queryset = queryset.filter(dataContrato__range=[data_inicio_periodo, data_fim_periodo])
                    
                elif periodo == 'ano':
                    data_inicio_periodo = timezone.make_aware(datetime(hoje.year, 1, 1, 0, 0, 0))
                    data_fim_periodo = timezone.make_aware(datetime(hoje.year, 12, 31, 23, 59, 59))
                    queryset = queryset.filter(dataContrato__range=[data_inicio_periodo, data_fim_periodo])
                    
                else:
                    return Response({"error": "Período inválido. Use: 'hoje', 'semana', 'mes' ou 'ano'"}, status=400)
            
            # Filtro por intervalo de datas específico
            else:
                try:
                    if data_inicio:
                        # Precisa de teste posteriormente 2
                        data_inicio_valor = datetime(data_inicio) or date(data_inicio)
                        if data_inicio_valor:
                            data_inicio_dt = timezone.make_aware(datetime.combine(data_inicio_valor, datetime.min.time()))
                            queryset = queryset.filter(dataContrato__gte=data_inicio_dt)
                    
                    if data_fim:
                        # Precisa de teste posteriormente 3
                        data_fim_valor = datetime(data_fim) or date(data_fim)
                        if data_fim_valor:
                            data_fim_dt = timezone.make_aware(datetime.combine(data_fim_valor, datetime.max.time()))
                            queryset = queryset.filter(dataContrato__lte=data_fim_dt)
                            
                except (ValueError, TypeError):
                    return Response({"error": "Formato de data inválido. Use YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS"}, status=400)

        # ---------------- ORDENAÇÃO ----------------
        # Adicione os novos campos ao order_mapping
        order_mapping = {
            'clienteId': 'clienteId__nome',
            '-clienteId': '-clienteId__nome',
            'advogadoCriadorId': 'advogadoCriadorId__nome',
            '-advogadoCriadorId': '-advogadoCriadorId__nome',
            'fase': 'fase__nome',
            '-fase': '-fase__nome',
            # Mapeamento para novos campos de tarefas
            'total_tarefas': 'total_tarefas',
            '-total_tarefas': '-total_tarefas',
            'tarefas_em_aberto': 'tarefas_em_aberto',
            '-tarefas_em_aberto': '-tarefas_em_aberto',
            'tarefas_atrasadas': 'tarefas_atrasadas',
            '-tarefas_atrasadas': '-tarefas_atrasadas',
            'tarefas_concluidas': 'tarefas_concluidas',
            '-tarefas_concluidas': '-tarefas_concluidas',
            'tarefas_urgentes': 'tarefas_urgentes',
            '-tarefas_urgentes': '-tarefas_urgentes',
            'tarefas_perto_prazo': 'tarefas_perto_prazo',
            '-tarefas_perto_prazo': '-tarefas_perto_prazo',
        }
        
        if order_by:
            try:
                if order_by in order_mapping:
                    queryset = queryset.order_by(order_mapping[order_by])
                else:
                    field_to_check = order_by.lstrip('-')
                    
                    if field_to_check in ['clienteId', 'advogadoCriadorId', 'fase', 
                                         'total_tarefas', 'tarefas_em_aberto', 'tarefas_atrasadas',
                                         'tarefas_concluidas', 'tarefas_urgentes', 'tarefas_perto_prazo']:
                        if order_by in order_mapping:
                            queryset = queryset.order_by(order_mapping[order_by])
                        elif f'-{field_to_check}' in order_mapping and order_by.startswith('-'):
                            queryset = queryset.order_by(order_mapping[f'-{field_to_check}'])
                        else:
                            queryset = queryset.order_by(order_by)
                    else:
                        queryset = queryset.order_by(order_by)
            except Exception as e:
                return Response({"error": f"Campo de ordenação inválido: {str(e)}"}, status=400)
        else:
            queryset = queryset.order_by('-prioritario', 'dataContrato')

        # ---------------- PAGINAÇÃO ----------------
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    
    
class GrupoAcaoViewSet(viewsets.ModelViewSet):
    queryset = GrupoAcao.objects.all()
    serializer_class = GrupoAcaoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = standardResultsSetPagination  # Adiciona a paginação
    
    def get_queryset(self):
        """
        Annota o queryset com as contagens de processos.
        """
        queryset = GrupoAcao.objects.annotate(
            total_processos=Count(
                'processo',
                distinct=True,
            ),
            arquivados=Count(
                'processo',
                distinct=True,
                filter=Q(processo__status='arquivado')
            ),
            concluidos=Count(
                'processo',
                distinct=True,
                filter=Q(processo__concluido=True)
            ),
            pendentes=Count(
                'processo',
                distinct=True,
                filter=Q(processo__concluido=False) & 
                       Q(processo__status='ativo')
            ),
            urgentes=Count(
                'processo',
                distinct=True,
                filter=Q(processo__prioritario=True) & 
                       Q(processo__concluido=False) & 
                       Q(processo__status='ativo')
            )
        )
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Parâmetros de filtro e ordenação
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')

        # Campos permitidos para busca
        allowed_fields = ['nome']
        
        # Queryset base com annotate
        queryset = self.get_queryset()
        
        # Filtro por campo e valor
        if field and value:
            if field not in allowed_fields:
                return Response({"error": "Campo de filtro inválido."}, status=400)

            # Filtro por nome
            if field == 'nome':
                queryset = queryset.filter(nome__icontains=value)
        
        # Ordenação
        if order_by:
            # Permite ordenar pelos campos annotados também
            annotate_fields = [
                'total_processos', '-total_processos',
                'arquivados', '-arquivados',
                'concluidos', '-concluidos',
                'pendentes', '-pendentes',
                'urgentes', '-urgentes'
            ]
            
            if order_by in annotate_fields:
                queryset = queryset.order_by(order_by)
            else:
                # Ordenação por campos do modelo
                if order_by.startswith('-'):
                    field_name = order_by[1:]
                    if field_name in ['nome']:
                        queryset = queryset.order_by(order_by)
                    else:
                        queryset = queryset.order_by(order_by)
                else:
                    if order_by in ['nome']:
                        queryset = queryset.order_by(order_by)
                    else:
                        queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('nome')  # Ordenação padrão por nome
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Sem paginação
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TipoAcaoViewSet(viewsets.ModelViewSet):
    queryset = TipoAcao.objects.all()
    serializer_class = TipoAcaoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = standardResultsSetPagination  # Adiciona paginação
    
    def get_queryset(self):
        """
        Annota o queryset com as contagens de processos.
        """
        queryset = TipoAcao.objects.annotate(
            total_processos=Count(
                'processo',
                distinct=True,
            ),
            arquivados=Count(
                'processo',
                distinct=True,
                filter=Q(processo__status='arquivado')
            ),
            concluidos=Count(
                'processo',
                distinct=True,
                filter=Q(processo__concluido=True)
            ),
            pendentes=Count(
                'processo',
                distinct=True,
                filter=Q(processo__concluido=False) & 
                       Q(processo__status='ativo')
            ),
            urgentes=Count(
                'processo',
                distinct=True,
                filter=Q(processo__prioritario=True) & 
                       Q(processo__concluido=False) & 
                       Q(processo__status='ativo')
            )
        ).select_related('grupoAcao')  # Otimiza consultas relacionadas
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Parâmetros de filtro
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')
        
        # Campos permitidos para busca
        allowed_fields = ['nome', 'grupoAcao']
        
        # Queryset base com annotate
        queryset = self.get_queryset()
        
        # Filtro por campo e valor
        if field and value:
            if field not in allowed_fields:
                raise ValidationError({
                    "error": f"O campo '{field}' não é permitido para busca."
                })
            
            # Filtro especial para grupoAcao
            if field == 'grupoAcao':
                queryset = queryset.filter(grupoAcao__nome__icontains=value)
            else:
                queryset = queryset.filter(**{f"{field}__icontains": value})
        
        # Ordenação
        if order_by:
            # Permite ordenar pelos campos annotados
            annotate_fields = [
                'total_processos', '-total_processos',
                'arquivados', '-arquivados',
                'concluidos', '-concluidos',
                'pendentes', '-pendentes',
                'urgentes', '-urgentes',
                # Campos de relacionamento
                'grupoAcao__nome', '-grupoAcao__nome'
            ]
            
            if order_by in annotate_fields:
                queryset = queryset.order_by(order_by)
            else:
                # Valida se o campo é válido para ordenação
                valid_order_fields = ['id', 'nome']
                if order_by.startswith('-'):
                    field_name = order_by[1:]
                    if field_name in valid_order_fields:
                        queryset = queryset.order_by(order_by)
                    else:
                        # Fallback para ordenação padrão
                        queryset = queryset.order_by('id')
                else:
                    if order_by in valid_order_fields:
                        queryset = queryset.order_by(order_by)
                    else:
                        queryset = queryset.order_by('id')
        else:
            queryset = queryset.order_by('id')
            
        # Paginação    
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Sem paginação
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    
    
class FaseProcessoViewSet(viewsets.ModelViewSet):
    """
    Faz uma pesquisa e retorna uma lista de processos de acordo com os parâmetros fornecidos.
    
    
    """
    queryset = FaseProcesso.objects.all()
    serializer_class = FaseProcessoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = standardResultsSetPagination  # Use o nome correto aqui
    
    def get_queryset(self):
        """
        Annota o queryset com as contagens de processos.
        """
        queryset = FaseProcesso.objects.annotate(
            total_processos=Count(
                'processo',
                distinct=True,
            ),
            arquivados=Count(
                'processo',
                distinct=True,
                filter=Q(processo__status='arquivado')
            ),
            concluidos=Count(
                'processo',
                distinct=True,
                filter=Q(processo__concluido=True)
            ),
            pendentes=Count(
                'processo',
                distinct=True,
                filter=Q(processo__concluido=False) & 
                       Q(processo__status='ativo')
            ),
            urgentes=Count(
                'processo',
                distinct=True,
                filter=Q(processo__prioritario=True) & 
                       Q(processo__concluido=False) & 
                       Q(processo__status='ativo')
            )
        )
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Parâmetros de filtro
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')
        
        # Campos permitidos para busca
        allowed_fields = ['nome']
        
        # Queryset base com annotate
        queryset = self.get_queryset()
        
        # Filtro por campo e valor
        if field and value:
            if field not in allowed_fields:
                raise ValidationError({
                    "error": f"O campo '{field}' não é permitido para busca."
                })
            
            # Filtro por nome
            queryset = queryset.filter(**{f"{field}__icontains": value})
        
        # Ordenação
        if order_by:
            # Permite ordenar pelos campos annotados
            annotate_fields = [
                'total_processos', '-total_processos',
                'arquivados', '-arquivados',
                'concluidos', '-concluidos',
                'pendentes', '-pendentes',
                'urgentes', '-urgentes'
            ]
            
            if order_by in annotate_fields:
                queryset = queryset.order_by(order_by)
            else:
                # Valida se o campo é válido para ordenação
                valid_order_fields = ['id', 'nome']
                if order_by.startswith('-'):
                    field_name = order_by[1:]
                    if field_name in valid_order_fields:
                        queryset = queryset.order_by(order_by)
                    else:
                        queryset = queryset.order_by('id')
                else:
                    if order_by in valid_order_fields:
                        queryset = queryset.order_by(order_by)
                    else:
                        queryset = queryset.order_by('id')
        else:
            queryset = queryset.order_by('id')
            
        # Paginação    
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Sem paginação
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    
    
class EtapaProcessoViewSet(viewsets.ModelViewSet):
    queryset = EtapaProcesso.objects.all()
    serializer_class = EtapaProcessoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = standardResultsSetPagination  # Use o nome correto aqui
    
    def get_queryset(self):
        """
        Annota o queryset com as contagens de processos.
        """
        queryset = EtapaProcesso.objects.annotate(
            total_processos=Count(
                'processo',
                distinct=True,
            ),
            arquivados=Count(
                'processo',
                distinct=True,
                filter=Q(processo__status='arquivado')
            ),
            concluidos=Count(
                'processo',
                distinct=True,
                filter=Q(processo__concluido=True)
            ),
            pendentes=Count(
                'processo',
                distinct=True,
                filter=Q(processo__concluido=False) & 
                       Q(processo__status='ativo')
            ),
            urgentes=Count(
                'processo',
                distinct=True,
                filter=Q(processo__prioritario=True) & 
                       Q(processo__concluido=False) & 
                       Q(processo__status='ativo')
            )
        ).select_related('faseProcesso')  # Otimiza consultas relacionadas
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Parâmetros de filtro
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')
        
        # Campos permitidos para busca
        allowed_fields = ['nome', 'faseProcesso']
        
        # Queryset base com annotate
        queryset = self.get_queryset()
        
        # Filtro por campo e valor
        if field and value:
            if field not in allowed_fields:
                raise ValidationError({
                    "error": f"O campo '{field}' não é permitido para busca."
                })
            
            # Filtro especial para faseProcesso
            if field == 'faseProcesso':
                queryset = queryset.filter(faseProcesso__nome__icontains=value)
            else:
                queryset = queryset.filter(**{f"{field}__icontains": value})
        
        # Ordenação
        if order_by:
            # Permite ordenar pelos campos annotados
            annotate_fields = [
                'total_processos', '-total_processos',
                'arquivados', '-arquivados',
                'concluidos', '-concluidos',
                'pendentes', '-pendentes',
                'urgentes', '-urgentes',
                # Campos de relacionamento
                'faseProcesso__nome', '-faseProcesso__nome'
            ]
            
            if order_by in annotate_fields:
                queryset = queryset.order_by(order_by)
            else:
                # Valida se o campo é válido para ordenação
                valid_order_fields = ['id', 'nome']
                if order_by.startswith('-'):
                    field_name = order_by[1:]
                    if field_name in valid_order_fields:
                        queryset = queryset.order_by(order_by)
                    else:
                        queryset = queryset.order_by('id')
                else:
                    if order_by in valid_order_fields:
                        queryset = queryset.order_by(order_by)
                    else:
                        queryset = queryset.order_by('id')
        else:
            queryset = queryset.order_by('id')
            
        # Paginação    
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Sem paginação
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
class TarefasViewSet(viewsets.ModelViewSet):
    queryset = Tarefas.objects.all()
    serializer_class = TarefasSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = standardResultsSetPagination

    def get_queryset(self):
        hoje = timezone.localdate()
        data_limite = hoje + timedelta(days=3)
        limite = datetime.combine(data_limite, time.max)  # até 23:59:59

        # Atualiza status de TODAS as tarefas (incluindo concluídas e deletadas)
        # Mas mantém o status das concluídas inalterado
        Tarefas.objects.filter(
            prazoFinal__lt=hoje,
            concluida=False
        ).update(status='atrasada')

        Tarefas.objects.filter(
            prazoFinal__gte=hoje,
            prazoFinal__lte=limite,
            concluida=False
        ).update(status='perto do prazo')

        Tarefas.objects.filter(
            prazoFinal__gt=limite,
            concluida=False
        ).update(status='em aberto')

        # NOVO: Otimiza as queries usando select_related para incluir cliente via processo
        return Tarefas.objects.select_related(
            'advogadoCriadorId',
            'advogadoResponsavelId',
            'tipoTarefa',
            'processoOrigemId',  # Inclui processo
            'processoOrigemId__clienteId'  # NOVO: Inclui cliente através do processo
        ).all()
    
    def list(self, request, *args, **kwargs):
        # Começa com todas as tarefas (já otimizadas)
        queryset = self.get_queryset()
        
        # Parâmetros de filtro e ordenação
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')
        
        # Filtros principais
        concluida = request.query_params.get('concluida')
        deletada = request.query_params.get('deletada')
        status = request.query_params.get('status')
        urgente = request.query_params.get('urgente')
        
        # NOVO: Filtro por ID do cliente (opcional)
        cliente_id = request.query_params.get('cliente_id')
        
        # Filtros por ID de relacionamentos
        advogado_responsavel_id = request.query_params.get('advogado_responsavel_id')
        advogado_criador_id = request.query_params.get('advogado_criador_id')
        processo_origem_id = request.query_params.get('processo_origem_id')
        
        allowed_fields = [
            'advogadoCriadorId',
            'advogadoResponsavelId',
            'processoOrigemId',
            'clienteNome'  # NOVO: Permite filtrar por nome do cliente
        ]
        
        # Filtro por campo composto (FK) - somente se ambos field e value forem fornecidos
        if field and value:
            if field not in allowed_fields:
                return Response({"error": "Campo de filtro inválido."}, status=400)
            match field:
                case 'advogadoCriadorId':
                    queryset = queryset.filter(advogadoCriadorId__nome__icontains=value)
                case 'advogadoResponsavelId':
                    queryset = queryset.filter(advogadoResponsavelId__nome__icontains=value)
                case 'processoOrigemId':
                    queryset = queryset.filter(processoOrigemId__numeroProcesso__icontains=value)
                case 'clienteNome':  # NOVO: Filtro por nome do cliente
                    queryset = queryset.filter(processoOrigemId__clienteId__nome__icontains=value)
        # Se apenas field for fornecido sem value, retorna erro
        elif field and not value:
            return Response({"error": "Parâmetro 'value' é obrigatório quando 'field' é fornecido."}, status=400)
        elif not field and value:
            return Response({"error": "Parâmetro 'field' é obrigatório quando 'value' é fornecido."}, status=400)
        
        # NOVO: Filtro por ID do cliente
        if cliente_id is not None:
            try:
                cliente_id_int = int(cliente_id)
                queryset = queryset.filter(processoOrigemId__clienteId__id=cliente_id_int)
            except ValueError:
                return Response(
                    {"error": "ID do cliente deve ser um número válido."}, 
                    status=400
                )
        
        # Filtro por ID do advogado responsável
        if advogado_responsavel_id is not None:
            try:
                advogado_id = int(advogado_responsavel_id)
                queryset = queryset.filter(advogadoResponsavelId__id=advogado_id)
            except ValueError:
                return Response(
                    {"error": "ID do advogado responsável deve ser um número válido."}, 
                    status=400
                )
        
        # Filtro por ID do advogado criador
        if advogado_criador_id is not None:
            try:
                advogado_id = int(advogado_criador_id)
                queryset = queryset.filter(advogadoCriadorId__id=advogado_id)
            except ValueError:
                return Response(
                    {"error": "ID do advogado criador deve ser um número válido."}, 
                    status=400
                )
        
        # Filtro por ID do processo de origem
        if processo_origem_id is not None:
            try:
                processo_id = int(processo_origem_id)
                queryset = queryset.filter(processoOrigemId__id=processo_id)
            except ValueError:
                return Response(
                    {"error": "ID do processo de origem deve ser um número válido."}, 
                    status=400
                )
        
        # Filtro por concluida - somente se o parâmetro for fornecido
        if concluida is not None:
            if concluida.lower() in ['true', '1', 'yes', 'verdadeiro', 'sim']:
                queryset = queryset.filter(concluida=True)
            elif concluida.lower() in ['false', '0', 'no', 'falso', 'não', 'nao']:
                queryset = queryset.filter(concluida=False)
            else:
                return Response(
                    {"error": "Valor inválido para 'concluida'. Use 'true' ou 'false'."}, 
                    status=400
                )
        
        # Filtro por deletada - somente se o parâmetro for fornecido
        if deletada is not None:
            if deletada.lower() in ['true', '1', 'yes', 'verdadeiro', 'sim']:
                queryset = queryset.filter(deletada=True)
            elif deletada.lower() in ['false', '0', 'no', 'falso', 'não', 'nao']:
                queryset = queryset.filter(deletada=False)
            else:
                return Response(
                    {"error": "Valor inválido para 'deletada'. Use 'true' ou 'false'."}, 
                    status=400
                )
        
        # Filtro por status - somente se o parâmetro for fornecido
        if status is not None:
            valid_statuses = ['em aberto', 'atrasada', 'perto do prazo']
            if status not in valid_statuses:
                return Response(
                    {"error": f"Status inválido. Status válidos: {', '.join(valid_statuses)}"}, 
                    status=400
                )
            queryset = queryset.filter(status=status)

        # Filtro por urgente - somente se o parâmetro for fornecido
        if urgente is not None:
            if urgente.lower() in ['true', '1', 'yes', 'verdadeiro', 'sim']:
                queryset = queryset.filter(urgente=True)
            elif urgente.lower() in ['false', '0', 'no', 'falso', 'não', 'nao']:
                queryset = queryset.filter(urgente=False)
            else:
                return Response(
                    {"error": "Valor inválido para 'urgente'. Use 'true' ou 'false'."}, 
                    status=400
                )
        
        # Ordenação
        if order_by:
            if order_by == 'advogadoCriadorId':
                queryset = queryset.order_by('advogadoCriadorId__nome')
            elif order_by == 'advogadoResponsavelId':
                queryset = queryset.order_by('advogadoResponsavelId__nome')
            elif order_by == 'processoOrigemId':
                queryset = queryset.order_by('processoOrigemId__numeroProcesso')
            elif order_by == 'clienteNome':  # NOVO: Ordenação por nome do cliente
                queryset = queryset.order_by('processoOrigemId__clienteId__nome')
            else:
                # Tenta ordenar pelo campo especificado
                try:
                    queryset = queryset.order_by(order_by)
                except FieldError:
                    # Se houver erro, mantém ordenação padrão
                    queryset = queryset.order_by('-urgente', 'prazoFinal')
        else:
            # Ordenação padrão SEMPRE aplicada
            queryset = queryset.order_by('-urgente', 'prazoFinal')
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
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
    permission_classes = [IsAuthenticated]
    pagination_class = standardResultsSetPagination
    
    def get_queryset(self):
        # Annota o queryset base com todas as estatísticas necessárias
        queryset = TipoTarefa.objects.annotate(
            total_tarefas=Count(
                'tarefas',
                filter=Q(tarefas__deletada=False)
            ),
            # Contagens gerais
            concluidas=Count(
                'tarefas',
                filter=Q(tarefas__concluida=True, tarefas__deletada=False)
            ),
            pendentes=Count(
                'tarefas',
                filter=Q(tarefas__concluida=False, tarefas__deletada=False)
            ),
            # Detalhes das pendentes (tarefas não concluídas)
            pendentes_em_aberto=Count(
                'tarefas',
                filter=Q(
                    tarefas__concluida=False,
                    tarefas__status='em aberto',
                    tarefas__deletada=False
                )
            ),
            pendentes_atrasadas=Count(
                'tarefas',
                filter=Q(
                    tarefas__concluida=False,
                    tarefas__status='atrasada',
                    tarefas__deletada=False
                )
            ),
            pendentes_perto_prazo=Count(
                'tarefas',
                filter=Q(
                    tarefas__concluida=False,
                    tarefas__status='perto do prazo',
                    tarefas__deletada=False
                )
            ),
            pendentes_urgentes=Count(
                'tarefas',
                filter=Q(
                    tarefas__concluida=False,
                    tarefas__urgente=True,
                    tarefas__deletada=False
                )
            ),
        )
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Parâmetros de filtro e ordenação
        search = request.query_params.get('search')
        order_by = request.query_params.get('order_by')
        
        # Queryset base com annotate
        queryset = self.get_queryset()
        
        # Filtro por nome (similar ao 'search' que você já tinha)
        if search:
            queryset = queryset.filter(nome__icontains=search)
        
        # Ordenação
        if order_by:
            # Campos permitidos para ordenação
            allowed_order_fields = [
                'id', 'nome', 
                'total_tarefas', 'concluidas', 'pendentes',
                'pendentes_em_aberto', 'pendentes_atrasadas', 
                'pendentes_perto_prazo', 'pendentes_urgentes'
            ]
            
            # Verifica se é ordenação descendente
            if order_by.startswith('-'):
                field_name = order_by[1:]
            else:
                field_name = order_by
            
            # Valida o campo de ordenação
            if field_name not in allowed_order_fields:
                return Response({
                    "error": f"Campo de ordenação inválido. Campos permitidos: {', '.join(allowed_order_fields)}"
                }, status=400)
            
            queryset = queryset.order_by(order_by)
        else:
            # Ordenação padrão por nome
            queryset = queryset.order_by('nome')
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # Sem paginação
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    
    
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
        advogados_online = Advogado.objects.filter(is_online=True)
        serializer = AdvogadoSerializer(advogados_online, many=True)
        return Response(serializer.data)


class AdvogadoLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.is_online = False
        user.save()
        return Response({"detail": "Logout realizado com sucesso."})
        #implementar o logout baseado no tempo do Token JWT


class BuscarClienteCamposView(APIView):
    permission_classes = [IsAuthenticated]
    alowed_field = ['nome','cpf','telefone','inss','parceiro']
    pagination_class = standardResultsSetPagination
    def get(self, request):
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')
        
        if not field or not value: 
            raise ValueError({
                "error": "Os campos 'field' e 'value' são obrigatórios."
            })
        if field not in self.alowed_field:
            raise ValueError({
                "error": f"O campo '{field}' não é permitido para busca."
            })
        if not order_by:
            if field == 'parceiro':
                queryset = Cliente.objects.filter(
                    parceiro__nome__icontains=value
                ).order_by('id')  
            else:     
                queryset = Cliente.objects.filter(**{f"{field}__contains": value}).order_by('id')
        else:
            if field == 'parceiro':
                queryset = Cliente.objects.filter(
                    parceiro__nome__icontains=value
                ).order_by(order_by)
            else:
                queryset = Cliente.objects.filter(**{f"{field}__contains": value}).order_by(order_by)
        return Response(ClienteSerializer(queryset, many=True).data)

#view para buscar processos por campo específico
class BuscarProcessoCampoView(APIView):
    permission_classes = [IsAuthenticated]
    alowed_field = ['titulo','numeroProcesso','advogadoCriadorId','clienteId','clienteNome']
    pagination_class = standardResultsSetPagination
    
    def get(self, request):
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')
        
        
        if not field or not value:
            raise ValidationError({
                "error": "Os campos 'field' e 'value' são obrigatórios."
            })
        if field not in self.alowed_field:
            raise ValidationError({
                "error": f"O campo '{field}' não é permitido para busca."
            })
        if not order_by:
            if field == 'advogadoCriadorId':
                queryset = Processo.objects.filter(
                    advogadoCriadorId__nome__icontains=value
                ).order_by('id')
            elif field == 'clienteNome':
                queryset = Processo.objects.filter(
                    clienteId__nome__icontains=value
                ).order_by('id')
            else:
                queryset = Processo.objects.filter(**{f"{field}__contains": value}).order_by('id')
            
        else:
            if field == 'advogadoCriadorId':
                queryset = Processo.objects.filter(
                    advogadoCriadorId__nome__icontains=value
                ).order_by(order_by)
            elif field == 'clienteId':
                queryset = Processo.objects.filter(
                    clienteId__nome__icontains=value
                ).order_by(order_by)
            else:
                queryset = Processo.objects.filter(**{f"{field}__contains": value}).order_by(order_by)
        return Response(ProcessoSerializer(queryset, many=True).data)   


class BuscarTarefaCampo(APIView):
    permission_classes = [IsAuthenticated]
    alowed_field = ['advogadoCriadorId','advogadoResponsavelId','processoOrigemId']

    def get(self, request):
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')
        if field not in self.alowed_field:
            raise ValidationError({
                "error": f"O campo '{field}' não é permitido para busca."
            })
        if not field or not value:
            raise ValidationError({
                "error": "Os campos 'field' e 'value' são obrigatórios."
            })
        if not order_by:
            if field == 'advogadoCriadorId':
                queryset = Tarefas.objects.filter(
                    advogadoCriadorId__nome__icontains=value
                ).order_by('id')
            elif field == 'advogadoResponsavelId':
                queryset = Tarefas.objects.filter(
                    advogadoResponsavelId__nome__icontains=value
                ).order_by('id')
            elif field == 'processoOrigemId':
                queryset = Tarefas.objects.filter(
                    processoOrigemId__titulo__icontains=value
                ).order_by('id')
        else:
            if field == 'advogadoCriadorId':
                queryset = Tarefas.objects.filter(
                    advogadoCriadorId__nome__icontains=value
                ).order_by(order_by)
            elif field == 'advogadoResponsavelId':
                queryset = Tarefas.objects.filter(
                    advogadoResponsavelId__nome__icontains=value
                ).order_by(order_by)
            elif field == 'processoOrigemId':
                queryset = Tarefas.objects.filter(
                    processoOrigemId__titulo__icontains=value
                ).order_by(order_by)
        return Response(TarefasSerializer(queryset, many=True).data)
            
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
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
        
        

@permission_classes([IsAuthenticated])
@csrf_exempt
def processosClientesNome(request, cliente_nome):
    if request.method == 'GET':
        if not cliente_nome:
            return JsonResponse({'error': 'Termo de busca obrigatório.'}, status=400)
        
        search_term = cliente_nome.strip()
        
        # Remove pontuação para busca numérica
        numeros_only = re.sub(r'[^0-9]', '', search_term)
        
        # Se tem apenas números (mesmo que parciais) OU se a string original contém números
        if numeros_only or any(c.isdigit() for c in search_term):
            # Busca por CPF (qualquer parte do CPF)
            clientes_por_cpf = Cliente.objects.filter(cpf__icontains=numeros_only) if numeros_only else Cliente.objects.none()
            
            # Busca por número do processo (qualquer parte do número)
            processos_por_numero = Processo.objects.filter(numeroProcesso__icontains=search_term)
            
            # Busca por nome (se o termo também contém letras)
            clientes_por_nome = Cliente.objects.none()
            if any(c.isalpha() for c in search_term):
                clientes_por_nome = Cliente.objects.filter(nome__icontains=search_term)
            
            # Combina os resultados de clientes (por CPF e por nome)
            clientes = (clientes_por_cpf | clientes_por_nome).distinct()
            
            # Processos: combina os encontrados por número + processos dos clientes encontrados
            processos_dos_clientes = Processo.objects.filter(clienteId__in=clientes) if clientes.exists() else Processo.objects.none()
            processos = (processos_por_numero | processos_dos_clientes).distinct()
            
        else:
            # Apenas letras - busca por nome do cliente
            clientes = Cliente.objects.filter(nome__icontains=search_term)
            processos = Processo.objects.filter(clienteId__in=clientes) if clientes.exists() else Processo.objects.none()
        
        # Se não encontrou nada
        if not clientes.exists() and not processos.exists():
            return JsonResponse({
                'error': 'Nenhum resultado encontrado.',
                'clientes': [],
                'processos': [],
                'total_clientes': 0,
                'total_processos': 0
            }, status=404)
        
        # Prepara os dados para retorno
        response_data = {
            'clientes': [],
            'processos': [],
            'total_clientes': clientes.count() if clientes else 0,
            'total_processos': processos.count() if processos else 0
        }
        
        # Processa clientes - GARANTINDO QUE É QUERYSET
        if clientes and clientes.exists():
            # Não converta para lista aqui! Mantenha como QuerySet
            clientes_limitados = clientes[:10]
            
            # Verificação de segurança
            if hasattr(clientes_limitados, 'values'):
                # É um QuerySet, pode usar values()
                response_data['clientes'] = list(clientes_limitados.values('id', 'nome', 'cpf'))
            else:
                # Se por algum motivo virou lista, constrói manualmente
                response_data['clientes'] = [
                    {'id': c.id, 'nome': c.nome, 'cpf': c.cpf} 
                    for c in clientes_limitados
                ]
        
        # Processa processos
        if processos and processos.exists():
            processos_limitados = processos.select_related('clienteId')[:10]
            
            processos_data = []
            for processo in processos_limitados:
                processos_data.append({
                    'id': processo.id,
                    'numero': processo.numeroProcesso,
                    'nomeCliente': processo.clienteId.nome if processo.clienteId else None,
                    'cpfCliente': processo.clienteId.cpf if processo.clienteId else None
                })
            response_data['processos'] = processos_data
        
        return JsonResponse(response_data, safe=False)
    
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

@csrf_exempt
def searchSelect(request):
    """
    Endpoint para busca em selects com suporte a relações hierárquicas.
    
    Query params:
    - search: termo de busca (opcional - vazio retorna todos)
    - tipo: grupo_acao, tipo_acao, fase_processo, etapa_processo (obrigatório)
    - id: ID do grupo (para tipo_acao) ou ID da fase (para etapa_processo) (opcional)
    - limit: limite de resultados (opcional, padrão 50)
    """
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    # Parâmetros obrigatórios
    tipo = request.GET.get('tipo')
    if not tipo:
        return JsonResponse({
            'error': 'Parâmetro "tipo" é obrigatório',
            'tipos_disponiveis': ['grupo_acao', 'tipo_acao', 'fase_processo', 'etapa_processo']
        }, status=400)
    
    # Valida o tipo
    tipos_validos = ['grupo_acao', 'tipo_acao', 'fase_processo', 'etapa_processo']
    if tipo not in tipos_validos:
        return JsonResponse({
            'error': f'Tipo "{tipo}" inválido',
            'tipos_disponiveis': tipos_validos
        }, status=400)
    
    # Parâmetros opcionais
    search = request.GET.get('search', '')
    id_param = request.GET.get('id')  # Parâmetro único 'id' vindo do front
    limit = request.GET.get('limit', 50)
    
    try:
        limit = int(limit)
        if limit > 200:  # Limite máximo para não sobrecarregar
            limit = 200
    except ValueError:
        limit = 50
    
    # Processa cada tipo
    if tipo == 'grupo_acao':
        return busca_grupo_acao(search, limit)
    
    elif tipo == 'tipo_acao':
        # Para tipo_acao, o id se refere ao grupo_id
        return busca_tipo_acao(search, id_param, limit)
    
    elif tipo == 'fase_processo':
        return busca_fase_processo(search, limit)
    
    elif tipo == 'etapa_processo':
        # Para etapa_processo, o id se refere ao fase_id
        return busca_etapa_processo(search, id_param, limit)
    
    return JsonResponse({'error': 'Erro interno'}, status=500)


def busca_grupo_acao(search, limit):
    """Busca em GrupoAcao"""
    queryset = GrupoAcao.objects.all()
    
    # Filtro de busca - se search vazio, retorna todos
    if search:
        queryset = queryset.filter(nome__icontains=search)
    
    # Ordenação e limite
    queryset = queryset.order_by('nome')[:limit]
    
    # Formata resposta
    resultados = [{'id': obj.id, 'nome': obj.nome} for obj in queryset]
    
    return JsonResponse({
        'tipo': 'grupo_acao',
        'resultados': resultados,
        'total': len(resultados)
    })


def busca_tipo_acao(search, id_param, limit):
    """Busca em TipoAcao, com filtro opcional por grupo usando o id_param"""
    queryset = TipoAcao.objects.all()
    
    # Filtro por grupo (opcional)
    if id_param:
        try:
            grupo_id = int(id_param)
            # Verifica se o grupo existe
            if not GrupoAcao.objects.filter(id=grupo_id).exists():
                return JsonResponse({
                    'error': f'Grupo com ID {grupo_id} não encontrado',
                    'tipo': 'tipo_acao'
                }, status=404)
            
            queryset = queryset.filter(grupoAcao_id=grupo_id)
        except ValueError:
            return JsonResponse({
                'error': 'id deve ser um número válido',
                'tipo': 'tipo_acao'
            }, status=400)
    
    # Filtro de busca - se search vazio, retorna todos (respeitando filtro de grupo)
    if search:
        queryset = queryset.filter(nome__icontains=search)
    
    # Ordenação e limite
    queryset = queryset.order_by('nome')[:limit]
    
    # Formata resposta com informação extra do grupo
    resultados = []
    for obj in queryset:
        item = {
            'id': obj.id,
            'nome': obj.nome,
            'grupo_id': obj.grupoAcao_id,
            'grupo_nome': obj.grupoAcao.nome if obj.grupoAcao else None
        }
        resultados.append(item)
    
    return JsonResponse({
        'tipo': 'tipo_acao',
        'resultados': resultados,
        'total': len(resultados),
        'filtro_aplicado': {
            'id': id_param
        }
    })


def busca_fase_processo(search, limit):
    """Busca em FaseProcesso"""
    queryset = FaseProcesso.objects.all()
    
    # Filtro de busca - se search vazio, retorna todos
    if search:
        queryset = queryset.filter(nome__icontains=search)
    
    # Ordenação e limite
    queryset = queryset.order_by('nome')[:limit]
    
    # Formata resposta
    resultados = [{'id': obj.id, 'nome': obj.nome} for obj in queryset]
    
    return JsonResponse({
        'tipo': 'fase_processo',
        'resultados': resultados,
        'total': len(resultados)
    })


def busca_etapa_processo(search, id_param, limit):
    """Busca em EtapaProcesso, com filtro opcional por fase usando o id_param"""
    queryset = EtapaProcesso.objects.all()
    
    # Filtro por fase (opcional)
    if id_param:
        try:
            fase_id = int(id_param)
            # Verifica se a fase existe
            if not FaseProcesso.objects.filter(id=fase_id).exists():
                return JsonResponse({
                    'error': f'Fase com ID {fase_id} não encontrada',
                    'tipo': 'etapa_processo'
                }, status=404)
            
            queryset = queryset.filter(faseProcesso_id=fase_id)
        except ValueError:
            return JsonResponse({
                'error': 'id deve ser um número válido',
                'tipo': 'etapa_processo'
            }, status=400)
    
    # Filtro de busca - se search vazio, retorna todos (respeitando filtro de fase)
    if search:
        queryset = queryset.filter(nome__icontains=search)
    
    # Ordenação e limite
    queryset = queryset.order_by('nome')[:limit]
    
    # Formata resposta com informação extra da fase
    resultados = []
    for obj in queryset:
        item = {
            'id': obj.id,
            'nome': obj.nome,
            'fase_id': obj.faseProcesso_id,
            'fase_nome': obj.faseProcesso.nome if obj.faseProcesso else None
        }
        resultados.append(item)
    
    return JsonResponse({
        'tipo': 'etapa_processo',
        'resultados': resultados,
        'total': len(resultados),
        'filtro_aplicado': {
            'id': id_param
        }
    })

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
        
        field = request.GET.get('field')
        value = request.GET.get('value')
        order_by = request.GET.get('order_by')
        
        page = request.GET.get('page', 1)
        page_size = int(request.GET.get('page_size', 10))
    
        allowed_field = ['nome', 'dataNascimento', 'sexo', 'email', 'telefone']

        # Validando o campo
        if field and value:
            if field not in allowed_field:
                raise ValidationError({
                    'error': f'O campo "{field}" nao é permitido para busca.'
                })
            # Query filtrando clientes sem contrato 
            clientes = Cliente.objects.filter(
                contrato = False
            ).filter(
                **{f"{field}__icontains": value}
            )
        else:
            # Query base
            clientes = Cliente.objects.filter(
                contrato = False
            )
       
           

        # intervalo de nascimentos para quem fará 65 anos em até 5 dias
        data65 = dataAtual - relativedelta(years=65)
        dataInicio = data65 - relativedelta(days=5)  # já fez (até 5 dias atrás)
        dataFim = data65 + relativedelta(days=5) 
        
        # aplicando prioridades
        clientes = clientes.annotate(
            prioridade=Case(
                When(
                    dataNascimento__range=(dataInicio, dataFim),
                    then=Value(1)
                ),
                default=Value(0),
                output_field=IntegerField()
            )
        )

        # Ordenação final
        if order_by:
            clientes = clientes.order_by('-prioridade', order_by)
        else:
            clientes = clientes.order_by('-prioridade', 'id')
            
        # Paginação
        paginator = Paginator(clientes, page_size)
        try:
            clientes = paginator.page(page)
        except PageNotAnInteger:
            clientes = paginator.page(1)
        except EmptyPage:
            clientes = paginator.page(paginator.num_pages)
        
        # Serialização
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
        processosRegulares = Processo.objects.filter(classificacao = 'regular').count()
        processosBons = Processo.objects.filter(classificacao = 'bom').count()
        processosExcelentes = Processo.objects.filter(classificacao = 'excelente').count()

        jsonFile = [
            {
                "classificacao":"ruim",
                "quantidade":processosRuins,
            },
            {
                "classificacao":"regular",
                "quantidade":processosRegulares,
            },
            {
                "classificacao":"bom",
                "quantidade":processosBons,
            },
            {
                "classificacao":"excelente",
                "quantidade":processosExcelentes,
            }

        ]
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)


@csrf_exempt
@permission_classes([IsAuthenticated])
def graficoProcessosGrupo(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

    # Agrupa e conta processos por grupo
    grupos = (
        GrupoAcao.objects
        .annotate(quantidade=Count('processo'))
        .values('nome', 'quantidade')
    )

    # Ajusta a estrutura do JSON
    json_file = [
        {
            "grupo": g['nome'],
            "quantidade": g['quantidade']
        }
        for g in grupos
    ]

    return JsonResponse(json_file, safe=False)

@csrf_exempt
@permission_classes([IsAuthenticated])
def graficosProcessosFase(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

    try:
        # Agrupa e conta processos por fase
        fases = (
            FaseProcesso.objects
            .annotate(quantidade=Count('processo'))  # Conta os processos relacionados
            .values('nome', 'quantidade')
            .order_by('nome')
        )

        # Estrutura do JSON
        json_data = [
            {
                "fase": fase['nome'],
                "quantidade": fase['quantidade']
            }
            for fase in fases
        ]

        return JsonResponse(json_data, safe=False)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@permission_classes([IsAuthenticated])        
def graficosProcessosProtocolarPeticionar(request):
    if request.method == 'GET':
        try:
            # Filtro case-insensitive para evitar problemas com maiúsculas/minúsculas
            processosProtocolar = Processo.objects.filter(tipoAcao__nome__iexact='protocolar').count()
            processosPeticionar = Processo.objects.filter(tipoAcao__nome__iexact='peticionar').count()

            jsonFile = [
                {
                    "categoria": "tipo_acao",
                    "protocolar": processosProtocolar,    
                    "peticionar": processosPeticionar,           
                },
            ]
            return JsonResponse(jsonFile, safe=False)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

        
@csrf_exempt
@permission_classes([IsAuthenticated])        
def graficoProcessosStatus(request):
    if request.method == 'GET':
        processosStatusAtivo = Processo.objects.filter(status = 'ativo').count()
        processoStatusArquivados = Processo.objects.filter(status = 'arquivado').count()
        jsonFile = [
            {
            "categoria":"atual",
            "ativos":processosStatusAtivo,    
            "arquivados":processoStatusArquivados,           
            },
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
                "categoria": "clientes",
                "comContrato": clientesComContrato,
                "semContrato": clientesSemContrato
            }
        ]
        return JsonResponse(jsonFile, safe=False)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

        
@csrf_exempt
@permission_classes([IsAuthenticated])
def graficoClientesParceiro(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

    parceiros = Parceiros.objects.annotate(quantidade_clientes=Count('clientes'))
    
    json_file = [
        {
            "parceiro": parceiro.nome,
            "quantidade": parceiro.quantidade_clientes
        }
        for parceiro in parceiros
    ]

    return JsonResponse(json_file, safe=False)

        
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

@csrf_exempt
@permission_classes([IsAuthenticated])
def parceiros_select(request):
    """
    Endpoint para listar parceiros no formato para select.
    Retorna apenas id e nome.
    """
    if request.method == 'GET':
        try:
            # Busca todos os parceiros, selecionando apenas id e nome
            parceiros = Parceiros.objects.all().values('id', 'nome')
            # Converte o QuerySet para lista
            parceiros_list = list(parceiros)
            return JsonResponse(parceiros_list, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

@csrf_exempt
@permission_classes([IsAuthenticated])
def representante_por_cliente(request, cliente_id):
    """
    Endpoint para buscar representante pelo ID do cliente.
    """
    if request.method == 'GET':
        try:
            # Verifica se o cliente existe
            cliente = Cliente.objects.get(id=cliente_id)
            
            # Busca o representante relacionado a este cliente
            representante = Representante.objects.filter(cliente=cliente_id).first()
            
            if not representante:
                return JsonResponse({'error': 'Nenhum representante encontrado para este cliente.'}, status=404)
            
            # Serializa os dados do representante
            serializer = RepresentanteSerializer(representante)
            return JsonResponse(serializer.data, safe=False)
            
        except Cliente.DoesNotExist:
            return JsonResponse({'error': 'Cliente não encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
@csrf_exempt
@permission_classes([IsAuthenticated])
def generic_select_view(request):
    """
    Versão em função - retorna {value, label} para selects do frontend
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        model_map = {
            'processo': Processo,
            'tipo_tarefa': TipoTarefa,
            'advogado': Advogado,
            'advogado-online': Advogado,  # Nova query para advogados online
            'cliente': Cliente,
            'parceiro': Parceiros,
            'representante': Representante,
            'escritorio': Escritorios,
            'grupo_acao': GrupoAcao,
            'fase_processo': FaseProcesso,
        }
        
        model_key = request.GET.get('model')
        
        if not model_key:
            return JsonResponse({
                "error": "Parâmetro 'model' é obrigatório",
                "models_disponiveis": list(model_map.keys())
            }, status=400)
        
        if model_key not in model_map:
            return JsonResponse({
                "error": f"Modelo '{model_key}' não disponível",
                "models_disponiveis": list(model_map.keys())
            }, status=400)
        
        model_class = model_map[model_key]
        
        # Inicializa o queryset
        if model_key == 'advogado-online':
            # Filtra apenas advogados online
            queryset = model_class.objects.filter(is_online=True, is_active=True)
        else:
            queryset = model_class.objects.all()
            
            # Filtra deletados/ativos (GrupoAcao não tem estes campos, então será ignorado)
            if hasattr(model_class, 'deletada'):
                queryset = queryset.filter(deletada=False)
            elif hasattr(model_class, 'ativo'):
                queryset = queryset.filter(ativo=True)
            elif hasattr(model_class, 'is_active'):
                # Para advogado normal, também filtra por is_active=True
                queryset = queryset.filter(is_active=True)
        
        # Busca
        search = request.GET.get('search', '')
        if search:
            # Tenta buscar por nome ou outros campos
            if hasattr(model_class, 'nome'):
                queryset = queryset.filter(nome__icontains=search)
            elif hasattr(model_class, 'name'):
                queryset = queryset.filter(name__icontains=search)
            elif hasattr(model_class, 'razao_social'):
                queryset = queryset.filter(razao_social__icontains=search)
        
        # Ordena
        if hasattr(model_class, 'nome'):
            queryset = queryset.order_by('nome')
        elif hasattr(model_class, 'name'):
            queryset = queryset.order_by('name')
        else:
            queryset = queryset.order_by('id')
        
        # Limite
        limit = request.GET.get('limit')
        if limit and limit.isdigit():
            limit_int = int(limit)
            queryset = queryset[:min(limit_int, 500)]
        
        # Formata resposta como {value, label}
        data = []
        for obj in queryset:
            # Determina o texto do label
            if hasattr(obj, 'nome'):
                label = obj.nome
            elif hasattr(obj, 'name'):
                label = obj.name
            elif hasattr(obj, 'razao_social'):
                label = obj.razao_social
            else:
                label = str(obj)
            
            # Adiciona campos extras opcionais
            extra_data = {}
            
            # Se quiser incluir o nome original também
            include_nome = request.GET.get('include_nome')
            if include_nome and include_nome.lower() == 'true':
                extra_data['nome'] = label
            
            # Se quiser incluir campo específico
            include_field = request.GET.get('include_field')
            if include_field and hasattr(obj, include_field):
                extra_data[include_field] = getattr(obj, include_field)
            
            # Para advogado-online, pode incluir o status online
            if model_key == 'advogado-online' or model_key == 'advogado':
                extra_data['is_online'] = obj.is_online
                extra_data['oab'] = obj.oab
            
            data.append({
                'value': obj.id,  # ← value é o ID
                'label': label,   # ← label é o nome/texto
                **extra_data  # Adiciona campos extras se houver
            })
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        return JsonResponse({
            "error": f"Erro interno: {str(e)}"
        }, status=500)