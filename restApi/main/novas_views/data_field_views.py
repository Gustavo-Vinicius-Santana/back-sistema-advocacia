
from rest_framework.permissions import IsAuthenticated
from .pagination_views import StandardResultsSetPagination
from ..models import Advogado,Escritorios,TipoTarefa,Representante,Parceiros,Tarefas,Cliente,Processo,GrupoAcao,TipoAcao,FaseProcesso,EtapaProcesso,Documentos,ArquivoModel,ArquivoTarefa,Tarefas,Cliente,GrupoAcao,TipoAcao,FaseProcesso,EtapaProcesso,Documentos,ArquivoModel,ArquivoTarefa,Processo
from ..serializers import GrupoAcaoSerializer,TipoAcaoSerializer,RepresentanteSerializer,TarefasSerializer,ClienteSerializer, FaseProcessoSerializer,EtapaProcessoSerializer,DocumentosSerializer,ArquivoModelSerializer,ArquivoTarefaSerializer,ProcessoSerializer
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

class BuscarClienteCamposView(APIView):
    permission_classes = [IsAuthenticated]
    alowed_field = ['nome','cpf','telefone','inss','parceiro']
    pagination_class = StandardResultsSetPagination
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
    pagination_class = StandardResultsSetPagination
    
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


class BuscarTarefaCampoView(APIView):
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
            
            
class BuscaSelect(APIView):
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
    
    def busca_tipo_acao(self, search, id_param, limit):
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
    
    def busca_fase_processo(self, search, limit):
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
    def busca_etapa_processo(self, search, id_param, limit):
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



class BuscaParceirosSelectView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(request):
        try:
            # Busca todos os parceiros, selecionando apenas id e nome
            parceiros = Parceiros.objects.all().values('id', 'nome')
            # Converte o QuerySet para lista
            parceiros_list = list(parceiros)
            return JsonResponse(parceiros_list, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    

class BuscarRepresentantesPorClienteView(APIView):
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
    
    
class BuscaGenericSelectView(APIView):
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