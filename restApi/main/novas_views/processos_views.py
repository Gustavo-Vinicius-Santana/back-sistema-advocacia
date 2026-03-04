from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from main.serializers import ProcessoSerializer,FaseProcessoSerializer,EtapaProcessoSerializer
from main.models import Processo, FaseProcesso, EtapaProcesso
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, date, datetime
from rest_framework.exceptions import ValidationError

class standardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


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
                        data_inicio_valor = datetime(data_inicio) or date(data_inicio)
                        if data_inicio_valor:
                            data_inicio_dt = timezone.make_aware(datetime.combine(data_inicio_valor, datetime.min.time()))
                            queryset = queryset.filter(dataContrato__gte=data_inicio_dt)
                    
                    if data_fim:
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