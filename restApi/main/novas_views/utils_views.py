from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .pagination_views import StandardResultsSetPagination
from django.db.models import Count, Q
from ..models import Tarefas,Cliente,GrupoAcao,TipoAcao,FaseProcesso,EtapaProcesso,Documentos,ArquivoModel,ArquivoTarefa,Processo
from ..serializers import TarefasSerializer,ClienteSerializer,GrupoAcaoSerializer,TipoAcaoSerializer, FaseProcessoSerializer,EtapaProcessoSerializer,DocumentosSerializer,ArquivoModelSerializer,ArquivoTarefaSerializer,ProcessoSerializer
from rest_framework.response import Response
from django.http import JsonResponse

from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

class GrupoAcaoViewSet(viewsets.ModelViewSet):
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
    

class EtapasPorFase(APIView):
    permission_classes = [IsAuthenticated]
    def get(request,fase_id):
        etapas = EtapaProcesso.objects.filter(faseProcesso=fase_id)
        serializer = EtapaProcessoSerializer(etapas, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)


class TipoPorGrupo(APIView):
    permission_classes = [IsAuthenticated]
    def get(request,grupo_id):
        tipo = TipoAcao.objects.filter(grupoAcao=grupo_id)
        serializer = TipoAcaoSerializer(tipo, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
