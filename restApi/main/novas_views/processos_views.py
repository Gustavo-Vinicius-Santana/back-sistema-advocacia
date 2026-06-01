from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from main.serializers import ProcessoSerializer,FaseProcessoSerializer,EtapaProcessoSerializer, ProcesssosResumidoSerializer
from main.models import Processo, FaseProcesso, EtapaProcesso,Cliente
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta, date, datetime
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
import json
from .services.processos_services import ProcessoService
from .permissions import *

class standardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProcessoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar processos.
    Lógica de filtro/ordenação delegada ao ProcessoService.
    """
    queryset = Processo.objects.all()
    serializer_class = ProcessoSerializer
    permission_classes = [OnlyAdminDELETE]
    pagination_class = standardResultsSetPagination

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = ProcessoService()

    def get_queryset(self):
        """Retorna queryset com anotações via service"""
        return self.service.get_queryset_anotado()

    def list(self, request, *args, **kwargs):
        """
        Lista processos com filtros avançados.

        Query params suportados:
        - cliente_id: ID do cliente
        - status: 'ativo', 'arquivado' ou 'ativo,arquivado'
        - concluido: 'true'/'false'
        - field: campo para filtro específico
        - value: valor para filtro
        - periodo: 'hoje', 'semana', 'mes', 'ano'
        - data_inicio/data_fim: intervalo de datas
        - order_by: campo para ordenação
        """
        try:
            # Delegar TODA a lógica de filtro ao service
            queryset = self.service.filtrar_e_ordenar_completos(
                cliente_id=request.query_params.get('cliente_id'),
                status=request.query_params.get('status'),
                concluido=request.query_params.get('concluido'),
                field=request.query_params.get('field'),
                value=request.query_params.get('value'),
                periodo=request.query_params.get('periodo'),
                data_inicio=request.query_params.get('data_inicio'),
                data_fim=request.query_params.get('data_fim'),
                order_by=request.query_params.get('order_by')
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        # Aplicar paginação
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
    permission_classes = [OnlyAdminDELETE]
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
    permission_classes = [OnlyAdminDELETE]
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


class ProcessosClientesView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = Processo.objects.all()
    serializer_class = ProcessoSerializer
    def get(request,cliente_id):
        if not cliente_id:
            return JsonResponse({'error':'Ciente não encontrado'})
        try:
            cliente = get_object_or_404(Cliente, id =cliente_id)
        except:
            return JsonResponse({'error':'Cliente nao encontrado'}, status=400)
        processos = Processo.objects.filter(clienteId=cliente)
        serializer = ProcessoSerializer(processos, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
    
class ProcessosArquivados(APIView):
    permission_classes = [OnlyAdminDELETE]
    queryset = Processo.objects.all()
    serializr_class = ProcessoSerializer
    
    def get(request,processo_id):
        if not processo_id:
            return JsonResponse({'error': 'ID do processo é obrigatório.'},status=400)
        try:
            processo = Processo.objects.get(id=processo_id,status='arquivado')
        except Processo.DoesNotExist:
            return JsonResponse({'error': 'Processo não encontrado ou não arquivado.'},status=404)
        serializer = ProcessoSerializer(processo)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    def put(request, processo_id):
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
    
    def patch(request,processo_id):
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
    
    
    def delete(request,processo_id):
        if not processo_id:
            return JsonResponse({'error': 'ID do processo é obrigatório.'},status=400)
        try:
            processo = Processo.objects.get(id=processo_id,status='arquivado')
        except Processo.DoesNotExist:
            return JsonResponse({'error': 'Processo nao encontrado ou nao arquivado.'},status=404)
        processo.delete()
        return JsonResponse({'message': 'Processo excluido com sucesso'}, status=201)
    
    
class ProcessosAdvogado(APIView):
    queryset = Processo.objects.all()
    serializer_class = ProcessoSerializer
    permission_classes = [OnlyAdminDELETE]
    
    def get(request,advogado_id):
        if not advogado_id:
            return JsonResponse({'error': 'ID do advogado é obrigatório.'})
        try:
            processo = Processo.objects.filter(advogadoResponsavelId=advogado_id)   
        except:
            return JsonResponse({'error': 'Advogado nao encontrado.'})
        serializer = ProcessoSerializer(processo, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)


class ProcessosResumidos(APIView):
    queryset = Processo.objects.all()
    serializer_class = ProcesssosResumidoSerializer
    permission_classes = [IsAuthenticated]
    def get(request):
        processos = Processo.objects.all()
        serializer = ProcesssosResumidoSerializer(processos,many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile,safe=False)
    
    
    
class ProcessosConcluidosEspecificos(APIView):
    queryset = Processo.objects.all()
    serializer_class = ProcessoSerializer
    permission_classes = [IsAuthenticated]
    def get(request,processo_id):
        if not processo_id:
            return JsonResponse({'error': 'ID do processo é obrigatório.'},status=400)
        try:
            processo = Processo.objects.get(id=processo_id,concluido=True)
        except Processo.DoesNotExist:
            return JsonResponse({'error': 'Processo não encontrado ou não concluído.'},status=404)
        serializer = ProcessoSerializer(processo)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    def put(request,processo_id):
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
    def patch(request,processo_id):
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
        