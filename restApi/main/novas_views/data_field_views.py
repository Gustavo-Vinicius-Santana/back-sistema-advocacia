import re
from rest_framework.permissions import IsAuthenticated
from .pagination_views import StandardResultsSetPagination
from .services.data_field_services import DataFieldService
from ..models import (
    Advogado,
    Escritorios,
    TipoTarefa,
    Representante,
    Parceiros,
    Tarefas,
    Cliente,
    Processo,
    GrupoAcao,
    TipoAcao,
    FaseProcesso,
    EtapaProcesso,
    Documentos,
    ArquivoModel,
    ArquivoTarefa,
    Tarefas,
    Cliente,
    GrupoAcao,
    TipoAcao,
    FaseProcesso,
    EtapaProcesso,
    Documentos,
    ArquivoModel,
    ArquivoTarefa,
    Processo,
)
from ..serializers import (
    GrupoAcaoSerializer,
    TipoAcaoSerializer,
    RepresentanteSerializer,
    TarefasSerializer,
    ClienteSerializer,
    FaseProcessoSerializer,
    EtapaProcessoSerializer,
    DocumentosSerializer,
    ArquivoModelSerializer,
    ArquivoTarefaSerializer,
    ProcessoSerializer,
    TipoTarefaSerializer,
)
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
from .permissions import *


class GrupoAcaoViewSet(viewsets.ModelViewSet):
    queryset = GrupoAcao.objects.all()
    serializer_class = GrupoAcaoSerializer
    permission_classes = [IsSystemStaff]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = GrupoAcao.objects.annotate(
            total_processos=Count("processo", distinct=True),
            arquivados=Count(
                "processo", distinct=True, filter=Q(processo__status="arquivado")
            ),
            concluidos=Count(
                "processo", distinct=True, filter=Q(processo__concluido=True)
            ),
            pendentes=Count(
                "processo",
                distinct=True,
                filter=Q(processo__concluido=False) & Q(processo__status="ativo"),
            ),
            urgentes=Count(
                "processo",
                distinct=True,
                filter=Q(processo__prioritario=True)
                & Q(processo__concluido=False)
                & Q(processo__status="ativo"),
            ),
        )
        return queryset

    def list(self, request, *args, **kwargs):
        field = request.query_params.get("field")
        value = request.query_params.get("value")
        order_by = request.query_params.get("order_by")
        service = DataFieldService()
        queryset = service.filter_and_order_queryset(
            self.get_queryset(),
            field,
            value,
            order_by,
            allowed_fields=["nome"],
            valid_order_fields=["nome"],
            annotate_fields=[
                "total_processos",
                "-total_processos",
                "arquivados",
                "-arquivados",
                "concluidos",
                "-concluidos",
                "pendentes",
                "-pendentes",
                "urgentes",
                "-urgentes",
            ],
            default_order="nome",
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TipoAcaoViewSet(viewsets.ModelViewSet):
    queryset = TipoAcao.objects.all()
    serializer_class = TipoAcaoSerializer
    permission_classes = [IsSystemStaff]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = TipoAcao.objects.annotate(
            total_processos=Count("processo", distinct=True),
            arquivados=Count(
                "processo", distinct=True, filter=Q(processo__status="arquivado")
            ),
            concluidos=Count(
                "processo", distinct=True, filter=Q(processo__concluido=True)
            ),
            pendentes=Count(
                "processo",
                distinct=True,
                filter=Q(processo__concluido=False) & Q(processo__status="ativo"),
            ),
            urgentes=Count(
                "processo",
                distinct=True,
                filter=Q(processo__prioritario=True)
                & Q(processo__concluido=False)
                & Q(processo__status="ativo"),
            ),
        ).select_related("grupoAcao")
        return queryset

    def list(self, request, *args, **kwargs):
        field = request.query_params.get("field")
        value = request.query_params.get("value")
        order_by = request.query_params.get("order_by")
        service = DataFieldService()
        queryset = service.filter_and_order_queryset(
            self.get_queryset(),
            field,
            value,
            order_by,
            allowed_fields=["nome", "grupoAcao"],
            valid_order_fields=["id", "nome", "grupoAcao__nome"],
            annotate_fields=[
                "total_processos",
                "-total_processos",
                "arquivados",
                "-arquivados",
                "concluidos",
                "-concluidos",
                "pendentes",
                "-pendentes",
                "urgentes",
                "-urgentes",
            ],
            special_filters={"grupoAcao": "grupoAcao__nome__icontains"},
            default_order="id",
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FaseProcessoViewSet(viewsets.ModelViewSet):
    queryset = FaseProcesso.objects.all()
    serializer_class = FaseProcessoSerializer
    permission_classes = [IsSystemStaff]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = FaseProcesso.objects.annotate(
            total_processos=Count("processo", distinct=True),
            arquivados=Count(
                "processo", distinct=True, filter=Q(processo__status="arquivado")
            ),
            concluidos=Count(
                "processo", distinct=True, filter=Q(processo__concluido=True)
            ),
            pendentes=Count(
                "processo",
                distinct=True,
                filter=Q(processo__concluido=False) & Q(processo__status="ativo"),
            ),
            urgentes=Count(
                "processo",
                distinct=True,
                filter=Q(processo__prioritario=True)
                & Q(processo__concluido=False)
                & Q(processo__status="ativo"),
            ),
        )
        return queryset

    def list(self, request, *args, **kwargs):
        field = request.query_params.get("field")
        value = request.query_params.get("value")
        order_by = request.query_params.get("order_by")
        service = DataFieldService()
        queryset = service.filter_and_order_queryset(
            self.get_queryset(),
            field,
            value,
            order_by,
            allowed_fields=["nome"],
            valid_order_fields=["id", "nome"],
            annotate_fields=[
                "total_processos",
                "-total_processos",
                "arquivados",
                "-arquivados",
                "concluidos",
                "-concluidos",
                "pendentes",
                "-pendentes",
                "urgentes",
                "-urgentes",
            ],
            default_order="id",
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class EtapaProcessoViewSet(viewsets.ModelViewSet):
    queryset = EtapaProcesso.objects.all()
    serializer_class = EtapaProcessoSerializer
    permission_classes = [IsSystemStaff]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = EtapaProcesso.objects.annotate(
            total_processos=Count("processo", distinct=True),
            arquivados=Count(
                "processo", distinct=True, filter=Q(processo__status="arquivado")
            ),
            concluidos=Count(
                "processo", distinct=True, filter=Q(processo__concluido=True)
            ),
            pendentes=Count(
                "processo",
                distinct=True,
                filter=Q(processo__concluido=False) & Q(processo__status="ativo"),
            ),
            urgentes=Count(
                "processo",
                distinct=True,
                filter=Q(processo__prioritario=True)
                & Q(processo__concluido=False)
                & Q(processo__status="ativo"),
            ),
        ).select_related("faseProcesso")
        return queryset

    def list(self, request, *args, **kwargs):
        field = request.query_params.get("field")
        value = request.query_params.get("value")
        order_by = request.query_params.get("order_by")
        service = DataFieldService()
        queryset = service.filter_and_order_queryset(
            self.get_queryset(),
            field,
            value,
            order_by,
            allowed_fields=["nome", "faseProcesso"],
            valid_order_fields=["id", "nome", "faseProcesso__nome"],
            annotate_fields=[
                "total_processos",
                "-total_processos",
                "arquivados",
                "-arquivados",
                "concluidos",
                "-concluidos",
                "pendentes",
                "-pendentes",
                "urgentes",
                "-urgentes",
            ],
            special_filters={"faseProcesso": "faseProcesso__nome__icontains"},
            default_order="id",
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TipoTarefaViewSet(viewsets.ModelViewSet):
    queryset = TipoTarefa.objects.all()
    serializer_class = TipoTarefaSerializer
    permission_classes = [IsSystemStaff]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = TipoTarefa.objects.annotate(
            total_tarefas=Count("tarefas", filter=Q(tarefas__deletada=False)),
            concluidas=Count(
                "tarefas", filter=Q(tarefas__concluida=True, tarefas__deletada=False)
            ),
            pendentes=Count(
                "tarefas", filter=Q(tarefas__concluida=False, tarefas__deletada=False)
            ),
            pendentes_em_aberto=Count(
                "tarefas",
                filter=Q(
                    tarefas__concluida=False,
                    tarefas__status="em aberto",
                    tarefas__deletada=False,
                ),
            ),
            pendentes_atrasadas=Count(
                "tarefas",
                filter=Q(
                    tarefas__concluida=False,
                    tarefas__status="atrasada",
                    tarefas__deletada=False,
                ),
            ),
            pendentes_perto_prazo=Count(
                "tarefas",
                filter=Q(
                    tarefas__concluida=False,
                    tarefas__status="perto do prazo",
                    tarefas__deletada=False,
                ),
            ),
            pendentes_urgentes=Count(
                "tarefas",
                filter=Q(
                    tarefas__concluida=False,
                    tarefas__urgente=True,
                    tarefas__deletada=False,
                ),
            ),
        )
        return queryset


class BuscaSelect(APIView):
    permission_classes = [OnlyAdminDELETE]

    def get(self, request):
        tipo = request.query_params.get("tipo")
        if not tipo:
            return JsonResponse({"error": "O campo 'tipo' é obrigatório."})
        tipos_validos = ["grupo_acao", "tipo_acao", "fase_processo", "etapa_processo"]
        if tipo not in tipos_validos:
            return JsonResponse(
                {
                    "error": f'Tipo "{tipo}" inválido',
                    "tipos_disponiveis": tipos_validos,
                },
                status=400,
            )
        search = request.GET.get("search", "")
        id_param = request.GET.get("id")
        limit = request.GET.get("limit", 50)
        try:
            limit = int(limit)
            if limit > 200:
                limit = 200
        except ValueError:
            limit = 50
        if tipo == "grupo_acao":
            return self.busca_grupo_acao(search, limit)
        elif tipo == "tipo_acao":
            return self.busca_tipo_acao(search, id_param, limit)
        elif tipo == "fase_processo":
            return self.busca_fase_processo(search, limit)
        elif tipo == "etapa_processo":
            return self.busca_etapa_processo(search, id_param, limit)
        return JsonResponse({"error": "Erro interno"}, status=500)

    def busca_grupo_acao(self, search, limit):
        queryset = GrupoAcao.objects.all()
        if search:
            queryset = queryset.filter(nome__icontains=search)
        queryset = queryset.order_by("nome")[:limit]
        resultados = [{"id": obj.id, "nome": obj.nome} for obj in queryset]
        return JsonResponse(
            {"tipo": "grupo_acao", "resultados": resultados, "total": len(resultados)}
        )

    def busca_tipo_acao(self, search, id_param, limit):
        queryset = TipoAcao.objects.all()
        if id_param:
            try:
                grupo_id = int(id_param)
                if not GrupoAcao.objects.filter(id=grupo_id).exists():
                    return JsonResponse(
                        {
                            "error": f"Grupo com ID {grupo_id} não encontrado",
                            "tipo": "tipo_acao",
                        },
                        status=404,
                    )
                queryset = queryset.filter(grupoAcao_id=grupo_id)
            except ValueError:
                return JsonResponse(
                    {"error": "id deve ser um número válido", "tipo": "tipo_acao"},
                    status=400,
                )
        if search:
            queryset = queryset.filter(nome__icontains=search)
        queryset = queryset.order_by("nome")[:limit]
        resultados = []
        for obj in queryset:
            item = {
                "id": obj.id,
                "nome": obj.nome,
                "grupo_id": obj.grupoAcao_id,
                "grupo_nome": obj.grupoAcao.nome if obj.grupoAcao else None,
            }
            resultados.append(item)
        return JsonResponse(
            {
                "tipo": "tipo_acao",
                "resultados": resultados,
                "total": len(resultados),
                "filtro_aplicado": {"id": id_param},
            }
        )

    def busca_fase_processo(self, search, limit):
        queryset = FaseProcesso.objects.all()
        if search:
            queryset = queryset.filter(nome__icontains=search)
        queryset = queryset.order_by("nome")[:limit]
        resultados = [{"id": obj.id, "nome": obj.nome} for obj in queryset]
        return JsonResponse(
            {
                "tipo": "fase_processo",
                "resultados": resultados,
                "total": len(resultados),
            }
        )

    def busca_etapa_processo(self, search, id_param, limit):
        queryset = EtapaProcesso.objects.all()
        if id_param:
            try:
                fase_id = int(id_param)
                if not FaseProcesso.objects.filter(id=fase_id).exists():
                    return JsonResponse(
                        {
                            "error": f"Fase com ID {fase_id} não encontrada",
                            "tipo": "etapa_processo",
                        },
                        status=404,
                    )
                queryset = queryset.filter(faseProcesso_id=fase_id)
            except ValueError:
                return JsonResponse(
                    {"error": "id deve ser um número válido", "tipo": "etapa_processo"},
                    status=400,
                )
        if search:
            queryset = queryset.filter(nome__icontains=search)
        queryset = queryset.order_by("nome")[:limit]
        resultados = []
        for obj in queryset:
            item = {
                "id": obj.id,
                "nome": obj.nome,
                "fase_id": obj.faseProcesso_id,
                "fase_nome": obj.faseProcesso.nome if obj.faseProcesso else None,
            }
            resultados.append(item)
        return JsonResponse(
            {
                "tipo": "etapa_processo",
                "resultados": resultados,
                "total": len(resultados),
                "filtro_aplicado": {"id": id_param},
            }
        )


class BuscaGenericSelectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(request):
        try:
            model_map = {
                "processo": Processo,
                "tipo_tarefa": TipoTarefa,
                "advogado": Advogado,
                "advogado-online": Advogado,
                "cliente": Cliente,
                "parceiro": Parceiros,
                "representante": Representante,
                "escritorio": Escritorios,
                "grupo_acao": GrupoAcao,
                "fase_processo": FaseProcesso,
            }
            model_key = request.GET.get("model")
            if not model_key:
                return JsonResponse(
                    {
                        "error": "Parâmetro 'model' é obrigatório",
                        "models_disponiveis": list(model_map.keys()),
                    },
                    status=400,
                )
            if model_key not in model_map:
                return JsonResponse(
                    {
                        "error": f"Modelo '{model_key}' não disponível",
                        "models_disponiveis": list(model_map.keys()),
                    },
                    status=400,
                )
            model_class = model_map[model_key]
            if model_key == "advogado-online":
                queryset = model_class.objects.filter(is_online=True, is_active=True)
            else:
                queryset = model_class.objects.all()
                if hasattr(model_class, "deletada"):
                    queryset = queryset.filter(deletada=False)
                elif hasattr(model_class, "ativo"):
                    queryset = queryset.filter(ativo=True)
                elif hasattr(model_class, "is_active"):
                    queryset = queryset.filter(is_active=True)
            search = request.GET.get("search", "")
            if search:
                if hasattr(model_class, "nome"):
                    queryset = queryset.filter(nome__icontains=search)
                elif hasattr(model_class, "name"):
                    queryset = queryset.filter(name__icontains=search)
                elif hasattr(model_class, "razao_social"):
                    queryset = queryset.filter(razao_social__icontains=search)
            if hasattr(model_class, "nome"):
                queryset = queryset.order_by("nome")
            elif hasattr(model_class, "name"):
                queryset = queryset.order_by("name")
            else:
                queryset = queryset.order_by("id")
            limit = request.GET.get("limit")
            if limit and limit.isdigit():
                limit_int = int(limit)
                queryset = queryset[: min(limit_int, 500)]
            data = []
            for obj in queryset:
                if hasattr(obj, "nome"):
                    label = obj.nome
                elif hasattr(obj, "name"):
                    label = obj.name
                elif hasattr(obj, "razao_social"):
                    label = obj.razao_social
                else:
                    label = str(obj)
                extra_data = {}
                include_nome = request.GET.get("include_nome")
                if include_nome and include_nome.lower() == "true":
                    extra_data["nome"] = label
                include_field = request.GET.get("include_field")
                if include_field and hasattr(obj, include_field):
                    extra_data[include_field] = getattr(obj, include_field)
                if model_key == "advogado-online" or model_key == "advogado":
                    extra_data["is_online"] = obj.is_online
                    extra_data["oab"] = obj.oab
                data.append({"value": obj.id, "label": label, **extra_data})
            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({"error": f"Erro interno: {str(e)}"}, status=500)


class BuscarRepresentantesPorClienteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, cliente_id):
        cliente = Cliente.objects.filter(id=cliente_id).first()
        if not cliente:
            return JsonResponse({"error": "Cliente nao encontrado"}, status=404)
        representante = Representante.objects.filter(cliente=cliente).first()
        if not representante:
            return JsonResponse(
                {"error": "Nenhum representante encontrado"}, status=404
            )
        serializer = RepresentanteSerializer(representante)
        return JsonResponse(serializer.data, safe=False)


class ProcessosClientesNomeView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = Processo.objects.all()
    serializer_class = ProcessoSerializer

    def get(self, request, cliente_nome):
        if not cliente_nome:
            return JsonResponse({"error": "Termo de busca obrigatório."}, status=400)
        search_term = cliente_nome.strip()
        if len(search_term) > 100:
            return JsonResponse({"error": "Termo de busca muito longo."}, status=400)
        numeros_only = re.sub("[^\\d]", "", search_term)
        clientes_encontrados = []
        processos_encontrados = []
        if any((c.isalpha() for c in search_term)):
            clientes_nome = Cliente.objects.filter(nome__icontains=search_term)
            clientes_encontrados.append(clientes_nome)
        if numeros_only:
            todos_clientes = Cliente.objects.all()
            clientes_cpf = []
            for cliente in todos_clientes:
                if cliente.cpf and numeros_only in self.limpar_cpf(cliente.cpf):
                    clientes_cpf.append(cliente.id)
            if clientes_cpf:
                clientes_encontrados.append(Cliente.objects.filter(id__in=clientes_cpf))
        clientes = Cliente.objects.none()
        for qs in clientes_encontrados:
            clientes = clientes | qs
        clientes = clientes.distinct()
        if search_term:
            processos_numero = Processo.objects.filter(
                numeroProcesso__icontains=search_term
            )
            processos_encontrados.append(processos_numero)
        if clientes.exists():
            processos_clientes = Processo.objects.filter(clienteId__in=clientes)
            processos_encontrados.append(processos_clientes)
        processos = Processo.objects.none()
        for qs in processos_encontrados:
            processos = processos | qs
        processos = processos.distinct()
        if not clientes.exists() and (not processos.exists()):
            return JsonResponse(
                {
                    "error": "Nenhum resultado encontrado.",
                    "clientes": [],
                    "processos": [],
                    "total_clientes": 0,
                    "total_processos": 0,
                },
                status=404,
            )
        response_data = {
            "clientes": [],
            "processos": [],
            "total_clientes": clientes.count(),
            "total_processos": processos.count(),
        }
        if clientes.exists():
            for cliente in clientes[:10]:
                response_data["clientes"].append(
                    {"id": cliente.id, "nome": cliente.nome, "cpf": cliente.cpf}
                )
        if processos.exists():
            for processo in processos.select_related("clienteId")[:10]:
                cliente = processo.clienteId
                response_data["processos"].append(
                    {
                        "id": processo.id,
                        "numero": processo.numeroProcesso,
                        "titulo": processo.titulo,
                        "status": processo.status,
                        "nomeCliente": cliente.nome if cliente else None,
                        "cpfCliente": cliente.cpf if cliente else None,
                        "clienteId": cliente.id if cliente else None,
                    }
                )
        return JsonResponse(response_data)

    def limpar_cpf(self, cpf):
        if not cpf:
            return ""
        return re.sub("[^\\d]", "", str(cpf))
