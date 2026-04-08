
import re
from rest_framework.permissions import IsAuthenticated
from .pagination_views import StandardResultsSetPagination
from ..models import Advogado,Escritorios,TipoTarefa,Representante,Parceiros,Tarefas,Cliente,Processo,GrupoAcao,TipoAcao,FaseProcesso,EtapaProcesso,Documentos,ArquivoModel,ArquivoTarefa,Tarefas,Cliente,GrupoAcao,TipoAcao,FaseProcesso,EtapaProcesso,Documentos,ArquivoModel,ArquivoTarefa,Processo
from ..serializers import GrupoAcaoSerializer,TipoAcaoSerializer,RepresentanteSerializer,TarefasSerializer,ClienteSerializer, FaseProcessoSerializer,EtapaProcessoSerializer,DocumentosSerializer,ArquivoModelSerializer,ArquivoTarefaSerializer,ProcessoSerializer,TipoTarefaSerializer
from rest_framework.response import Response
from django.http import JsonResponse
from django.db.models import Count, Q

from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from django.http import JsonResponse

from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView


class GrupoAcaoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar Grupos de Ação.
    
    Endpoint: /api/gruposAcao/
    
    Parâmetros GET:
    - field: Campo para filtrar (valores permitidos: 'nome')
    - value: Valor para buscar no campo especificado
    - order_by: Campo para ordenação (valores permitidos: 'total_processos', '-total_processos', 
      'arquivados', '-arquivados', 'concluidos', '-concluidos', 'pendentes', '-pendentes', 
      'urgentes', '-urgentes', 'nome', '-nome')
    
    Campos annotados disponíveis:
    - total_processos: Número total de processos associados
    - arquivados: Processos com status 'arquivado'
    - concluidos: Processos marcados como concluídos
    - pendentes: Processos não concluídos e com status 'ativo'
    - urgentes: Processos prioritários não concluídos e com status 'ativo'
    
    Métodos HTTP permitidos: GET, POST, PUT, PATCH, DELETE
    Autenticação: Requer usuário autenticado
    Paginação: Padrão (StandardResultsSetPagination)
    """
    queryset = GrupoAcao.objects.all()
    serializer_class = GrupoAcaoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination  # Adiciona a paginação
    
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
    """
    ViewSet para gerenciar Tipos de Ação.
    
    Endpoint: /api/tiposAcao/
    
    Parâmetros GET:
    - field: Campo para filtrar (valores permitidos: 'nome', 'grupoAcao')
    - value: Valor para buscar no campo especificado
    - order_by: Campo para ordenação (valores permitidos: 'total_processos', '-total_processos', 
      'arquivados', '-arquivados', 'concluidos', '-concluidos', 'pendentes', '-pendentes', 
      'urgentes', '-urgentes', 'id', '-id', 'nome', '-nome', 'grupoAcao__nome', '-grupoAcao__nome')
    
    Campos annotados disponíveis:
    - total_processos: Número total de processos associados
    - arquivados: Processos com status 'arquivado'
    - concluidos: Processos marcados como concluídos
    - pendentes: Processos não concluídos e com status 'ativo'
    - urgentes: Processos prioritários não concluídos e com status 'ativo'
    
    Métodos HTTP permitidos: GET, POST, PUT, PATCH, DELETE
    Autenticação: Requer usuário autenticado
    Paginação: Padrão (StandardResultsSetPagination)
    """
    queryset = TipoAcao.objects.all()
    serializer_class = TipoAcaoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination  # Adiciona paginação
    
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
    ViewSet para gerenciar Fases de Processo.
    
    Endpoint: /api/fasesProcesso/
    
    Parâmetros GET:
    - field: Campo para filtrar (valores permitidos: 'nome')
    - value: Valor para buscar no campo especificado (busca case-insensitive)
    - order_by: Campo para ordenação (valores permitidos: 'total_processos', '-total_processos', 
      'arquivados', '-arquivados', 'concluidos', '-concluidos', 'pendentes', '-pendentes', 
      'urgentes', '-urgentes', 'id', '-id', 'nome', '-nome')
    
    Campos annotados disponíveis:
    - total_processos: Número total de processos associados
    - arquivados: Processos com status 'arquivado'
    - concluidos: Processos marcados como concluídos
    - pendentes: Processos não concluídos e com status 'ativo'
    - urgentes: Processos prioritários não concluídos e com status 'ativo'
    
    Métodos HTTP permitidos: GET, POST, PUT, PATCH, DELETE
    Autenticação: Requer usuário autenticado
    Paginação: Padrão (StandardResultsSetPagination)
    """
    """
    Faz uma pesquisa e retorna uma lista de processos de acordo com os parâmetros fornecidos.
    
    
    """
    queryset = FaseProcesso.objects.all()
    serializer_class = FaseProcessoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination  # Use o nome correto aqui
    
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
    """
    ViewSet para gerenciar Etapas de Processo.
    
    Endpoint: /api/etapasProcesso/
    
    Parâmetros GET:
    - field: Campo para filtrar (valores permitidos: 'nome', 'faseProcesso')
    - value: Valor para buscar no campo especificado (busca case-insensitive)
    - order_by: Campo para ordenação (valores permitidos: 'total_processos', '-total_processos', 
      'arquivados', '-arquivados', 'concluidos', '-concluidos', 'pendentes', '-pendentes', 
      'urgentes', '-urgentes', 'id', '-id', 'nome', '-nome', 'faseProcesso__nome', '-faseProcesso__nome')
    
    Campos annotados disponíveis:
    - total_processos: Número total de processos associados
    - arquivados: Processos com status 'arquivado'
    - concluidos: Processos marcados como concluídos
    - pendentes: Processos não concluídos e com status 'ativo'
    - urgentes: Processos prioritários não concluídos e com status 'ativo'
    
    Métodos HTTP permitidos: GET, POST, PUT, PATCH, DELETE
    Autenticação: Requer usuário autenticado
    Paginação: Padrão (StandardResultsSetPagination)
    """
    queryset = EtapaProcesso.objects.all()
    serializer_class = EtapaProcessoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination  # Use o nome correto aqui
    
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

class TipoTarefaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar Tipos de Tarefa.
    
    Endpoint: /api/tipoTarefa/
    
    Campos annotados disponíveis:
    - total_tarefas: Número total de tarefas associadas (não deletadas)
    - concluidas: Tarefas marcadas como concluídas e não deletadas
    - pendentes: Tarefas não concluídas e não deletadas
    - pendentes_em_aberto: Tarefas não concluídas com status 'em aberto'
    - pendentes_atrasadas: Tarefas não concluídas com status 'atrasada'
    - pendentes_perto_prazo: Tarefas não concluídas com status 'perto do prazo'
    - pendentes_urgentes: Tarefas não concluídas marcadas como urgentes
    
    Métodos HTTP permitidos: GET, POST, PUT, PATCH, DELETE
    Autenticação: Requer usuário autenticado
    Paginação: Padrão (StandardResultsSetPagination)
    """
    queryset = TipoTarefa.objects.all()
    serializer_class = TipoTarefaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
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

class BuscaSelect(APIView):
    """
    View para busca específica em campos pesquisáveis.
    
    Endpoint: /api/select/
    
    Parâmetros GET:
    - tipo (obrigatório): Tipo de busca (valores permitidos: 'grupo_acao', 'tipo_acao', 'fase_processo', 'etapa_processo')
    - search (opcional): Termo para busca case-insensitive no nome
    - id (opcional): ID para filtro adicional
      - Para 'tipo_acao': filtra por grupoAcao_id
      - Para 'etapa_processo': filtra por faseProcesso_id
    - limit (opcional): Limite de resultados (padrão: 50, máximo: 200)
    
    Resposta JSON:
    - tipo: tipo da busca realizada
    - resultados: array com {id, nome} ou {id, nome, grupo_id, grupo_nome} ou {id, nome, fase_id, fase_nome}
    - total: número de resultados encontrados
    - filtro_aplicado: objeto com ID aplicado (quando aplicável)
    
    Métodos HTTP permitidos: GET
    Autenticação: Requer usuário autenticado
    """
    permission_classes = [IsAuthenticated]
    def get(self, request):
        tipo = request.query_params.get('tipo')
        if not tipo:
            return JsonResponse({
                "error": "O campo 'tipo' é obrigatório."
            })
        tipos_validos = ['grupo_acao', 'tipo_acao', 'fase_processo', 'etapa_processo']
        if tipo not in tipos_validos:
            return JsonResponse({
                "error": f'Tipo "{tipo}" inválido',
                "tipos_disponiveis": tipos_validos
            },status=400)
            
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
            return self.busca_grupo_acao(search, limit)

        elif tipo == 'tipo_acao':
        # Para tipo_acao, o id se refere ao grupo_id
            return self.busca_tipo_acao(search, id_param, limit)

        elif tipo == 'fase_processo':
            return self.busca_fase_processo(search, limit)

        elif tipo == 'etapa_processo':
        # Para etapa_processo, o id se refere ao fase_id
            return self.busca_etapa_processo(search, id_param, limit)

        return JsonResponse({'error': 'Erro interno'}, status=500)

    
    def busca_grupo_acao(self, search, limit):
        """
        Método auxiliar para busca em GrupoAcao.
        
        Parâmetros:
        - search: Termo para busca case-insensitive no nome (opcional)
        - limit: Número máximo de resultados
        
        Retorna: JsonResponse com tipo, resultados e total
        """
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
    
    def busca_tipo_acao(self, search, id_param, limit):
        """
        Método auxiliar para busca em TipoAcao com filtro opcional por grupo.
        
        Parâmetros:
        - search: Termo para busca case-insensitive no nome (opcional)
        - id_param: ID do grupoAcao para filtro (opcional)
        - limit: Número máximo de resultados
        
        Retorna: JsonResponse com tipo, resultados, total e filtro_aplicado
        """
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
    
    def busca_fase_processo(self, search, limit):
        """
        Método auxiliar para busca em FaseProcesso.
        
        Parâmetros:
        - search: Termo para busca case-insensitive no nome (opcional)
        - limit: Número máximo de resultados
        
        Retorna: JsonResponse com tipo, resultados e total
        """
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
    def busca_etapa_processo(self, search, id_param, limit):
        """
        Método auxiliar para busca em EtapaProcesso com filtro opcional por fase.
        
        Parâmetros:
        - search: Termo para busca case-insensitive no nome (opcional)
        - id_param: ID da faseProcesso para filtro (opcional)
        - limit: Número máximo de resultados
        
        Retorna: JsonResponse com tipo, resultados, total e filtro_aplicado
        """
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

class BuscaGenericSelectView(APIView):
    """
    View para busca genérica em múltiplos modelos.
    
    Endpoint: /api/search-select/
    
    Parâmetros GET:
    - model (obrigatório): Modelo para busca (valores permitidos: 'processo', 'tipo_tarefa', 
      'advogado', 'advogado-online', 'cliente', 'parceiro', 'representante', 'escritorio', 
      'grupo_acao', 'fase_processo')
    - search (opcional): Termo para busca case-insensitive
    - limit (opcional): Limite de resultados (padrão: sem limite, máximo: 500)
    - include_nome (opcional): Incluir campo 'nome' adicional (valores: 'true'/'false')
    - include_field (opcional): Incluir campo específico adicional
    
    Resposta JSON (array de objetos):
    - value: ID do objeto
    - label: Nome/texto de exibição
    - Campos extras baseados nos parâmetros include_* e tipo de modelo
    
    Filtros automáticos aplicados:
    - Models com campo 'deletada': filtra deletada=False
    - Models com campo 'ativo': filtra ativo=True
    - Models com campo 'is_active': filtra is_active=True
    - 'advogado-online': adicionalmente filtra is_online=True
    
    Métodos HTTP permitidos: GET
    Autenticação: Requer usuário autenticado
    """
    permission_classes = [IsAuthenticated]
    
    def get(request):
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

class BuscarRepresentantesPorClienteView(APIView):
    """
    View para buscar representantes de um cliente específico.
    
    Endpoint: /api/cliente/<int:cliente_id>/representante/
    
    Parâmetros URL:
    - cliente_id (obrigatório): ID do cliente para buscar representantes
    
    Resposta JSON:
    - Em caso de sucesso: dados completos do representante
    - Em caso de erro: {"error": "mensagem"} com status apropriado
    
    Códigos de status:
    - 200: Representante encontrado
    - 404: Cliente não encontrado ou nenhum representante associado
    
    Métodos HTTP permitidos: GET
    Autenticação: Requer usuário autenticado
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, cliente_id):
        cliente = Cliente.objects.filter(id=cliente_id).first()
        
        if not cliente:
            return JsonResponse({
                "error": "Cliente nao encontrado"
            }, status=404)
        
        representante = Representante.objects.filter(cliente=cliente).first()
        
        if not representante:
            return JsonResponse({
                "error": "Nenhum representante encontrado"
            }, status=404)
        
        serializer = RepresentanteSerializer(representante)
        return JsonResponse(serializer.data, safe=False)

class ProcessosClientesNomeView(APIView):
    """
    View unificada para busca de processos e clientes por nome, CPF ou número do processo.
    
    Endpoint: /api/processosClientesNome/<str:cliente_nome>/
    
    Parâmetros URL:
    - cliente_nome (obrigatório): Termo de busca (pode ser nome do cliente, CPF ou número do processo)
    
    Lógica de busca:
    1. Validação: termo obrigatório, máximo 100 caracteres
    2. Extração de números: remove pontuação para busca de CPF
    3. Busca por nome: se conter letras, busca em Cliente.nome
    4. Busca por CPF: compara números sem pontuação
    5. Busca por processo: busca em Processo.numeroProcesso
    6. Combina resultados: processos dos clientes encontrados + processos por número
    
    Resposta JSON:
    {
      "clientes": [{"id": int, "nome": str, "cpf": str}], // limite 10
      "processos": [{
        "id": int,
        "numero": str,
        "titulo": str,
        "status": str,
        "nomeCliente": str,
        "cpfCliente": str,
        "clienteId": int
      }], // limite 10
      "total_clientes": int,
      "total_processos": int
    }
    
    Códigos de status:
    - 200: Busca realizada com sucesso
    - 400: Termo de busca obrigatório ou muito longo
    - 404: Nenhum resultado encontrado
    
    Métodos HTTP permitidos: GET
    Autenticação: Requer usuário autenticado
    
    Método auxiliar:
    - limpar_cpf(cpf): Remove pontuação do CPF para comparação numérica
    """
    permission_classes = [IsAuthenticated]
    queryset = Processo.objects.all()
    serializer_class = ProcessoSerializer
    
    def get(self,request,cliente_nome):
        if not cliente_nome:
            return JsonResponse({'error': 'Termo de busca obrigatório.'}, status=400)
        
        search_term = cliente_nome.strip()
        
        # Limita o tamanho da busca
        if len(search_term) > 100:
            return JsonResponse({'error': 'Termo de busca muito longo.'}, status=400)
        
        # Prepara termo numérico (sem pontuação)
        numeros_only = re.sub(r'[^\d]', '', search_term)
        
        # Busca clientes
        clientes_encontrados = []
        processos_encontrados = []
        
        # Busca por nome (se tiver letras)
        if any(c.isalpha() for c in search_term):
            clientes_nome = Cliente.objects.filter(nome__icontains=search_term)
            clientes_encontrados.append(clientes_nome)
        
        # Busca por CPF (compara sem pontuação)
        if numeros_only:
            # Busca em todos os clientes e filtra por CPF sem pontuação
            todos_clientes = Cliente.objects.all()
            clientes_cpf = []
            
            for cliente in todos_clientes:
                if cliente.cpf and numeros_only in self.limpar_cpf(cliente.cpf):
                    clientes_cpf.append(cliente.id)
            
            if clientes_cpf:
                clientes_encontrados.append(Cliente.objects.filter(id__in=clientes_cpf))
        
        # Combina resultados de clientes
        clientes = Cliente.objects.none()
        for qs in clientes_encontrados:
            clientes = clientes | qs
        clientes = clientes.distinct()
        
        # Busca processos por número
        if search_term:
            processos_numero = Processo.objects.filter(numeroProcesso__icontains=search_term)
            processos_encontrados.append(processos_numero)
        
        # Busca processos dos clientes encontrados
        if clientes.exists():
            processos_clientes = Processo.objects.filter(clienteId__in=clientes)
            processos_encontrados.append(processos_clientes)
        
        # Combina processos
        processos = Processo.objects.none()
        for qs in processos_encontrados:
            processos = processos | qs
        processos = processos.distinct()
        
        # Se não encontrou nada
        if not clientes.exists() and not processos.exists():
            return JsonResponse({
                'error': 'Nenhum resultado encontrado.',
                'clientes': [],
                'processos': [],
                'total_clientes': 0,
                'total_processos': 0
            }, status=404)
        
        # Prepara resposta
        response_data = {
            'clientes': [],
            'processos': [],
            'total_clientes': clientes.count(),
            'total_processos': processos.count()
        }
        
        # Adiciona clientes (limite 10)
        if clientes.exists():
            for cliente in clientes[:10]:
                response_data['clientes'].append({
                    'id': cliente.id,
                    'nome': cliente.nome,
                    'cpf': cliente.cpf  # Mantém o formato original
                })
        
        # Adiciona processos (limite 10)
        if processos.exists():
            for processo in processos.select_related('clienteId')[:10]:
                cliente = processo.clienteId
                response_data['processos'].append({
                    'id': processo.id,
                    'numero': processo.numeroProcesso,
                    'titulo': processo.titulo,
                    'status': processo.status,
                    'nomeCliente': cliente.nome if cliente else None,
                    'cpfCliente': cliente.cpf if cliente else None,
                    'clienteId': cliente.id if cliente else None
                })
        
        return JsonResponse(response_data)
    
    def limpar_cpf(self,cpf):
        if not cpf:
            return ''
        return re.sub(r'[^\d]', '', str(cpf))
