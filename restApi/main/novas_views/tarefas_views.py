from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..serializers import TarefasSerializer,TipoTarefaSerializer,HistoricoTarefasSerializer
from ..models import Tarefas,TipoTarefa,HistoricoTarefas
from .pagination_views import StandardResultsSetPagination
from django.utils import timezone
from datetime import datetime, timedelta, time
from rest_framework import status
from django.core.exceptions import FieldError
from django.db.models import Q, Count
from django.http import JsonResponse
import json
from .services import TarefasServices
from .permissions import *

class TarefasViewSet(viewsets.ModelViewSet):
    service  = TarefasServices()
    queryset = service.obter_queryset()
    serializer_class = TarefasSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        service = TarefasServices()
        return service.custom_queryset()
    
    def list(self, request, *args, **kwargs):
        # Começa com todas as tarefas (já otimizadas)
        queryset = self.get_queryset()
        
        service = TarefasServices()
        try:
            queryset = service.list_services(request,queryset)

        except FieldError as e:
            return Response({'error': str(e)}, status=400)
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        service = TarefasServices()
        
        hoje = timezone.localdate()
        data = request.data.copy()
        data['dataInicio'] = hoje
        prazoFinal_str = data.get('prazoFinal')
        if prazoFinal_str < hoje.strftime('%Y-%m-%d'):
            response = {
                'error': 'A data de prazoFinal nao pode ser anterior a data de hoje.'
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        tiposLista = service.obter_tipos_tarefas() 
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
            service = TarefasServices()
            historico_criado = service.criar_historico_tarefa(tarefa_id, data_Hora, advogado_nome, campos_mudados_formatados)
            if not historico_criado:
                return Response({'error': 'Erro ao criar histórico da tarefa.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        return response
    

class TipoTarefaViewSet(viewsets.ModelViewSet):
    service = TarefasServices()
    queryset = service.obter_tipos_tarefas()
    serializer_class = TipoTarefaSerializer
    permission_classes = [OnlyAdminDELETE]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        # Annota o queryset base com todas as estatísticas necessárias
        service = TarefasServices()
        queryset = service.obter_tipos_tarefas()
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


class TarefasProcessosView(APIView):
    permission_classes = [OnlyAdminDELETE]
    
    def get(self, request, processo_id):
        if not processo_id:
            return JsonResponse({'error': 'ID do processo obrigatório.'}, status=400)
        service = TarefasServices()
        try:
            tarefas = service.obter_tarefas_por_processo(processo_id)
        except:
            return JsonResponse({'error': 'Processo não encontrado.'})
        
        serializer = TarefasSerializer(tarefas, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
    
class TarefasDeletadasView(APIView):
    permission_classes = [OnlyAdminDELETE]
    service = TarefasServices()
    queryset = service.obter_tarefas_deletadas()
    
    def get(self, request):
        service = TarefasServices()
        tarefas = service.obter_tarefas_deletadas()
        serializer = TarefasSerializer(tarefas, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
    
class TarefasDeletadasEspecificasView(APIView):
    service = TarefasServices()
    permission_classes = [OnlyAdminDELETE]
    queryset = service.obter_tarefas_deletadas()
    
    def get(self, request, tarefa_id):
        service = TarefasServices()
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)
        try:
            tarefa = service.obter_tarefas_deletadas_por_id(tarefa_id)      
        except:
            return JsonResponse({'error': 'Tarefa nao encontrada.'})
        
        serializer = TarefasSerializer(tarefa)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
    def patch(self,request,tarefa_id):
        service = TarefasServices()
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)     
        try:
            tarefa = service.obter_tarefas_deletadas_por_id(tarefa_id)
        except Exception as e:
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
    
    def delete(self,request,tarefa_id):
        service = TarefasServices()
        if not tarefa_id:
            return JsonResponse({'error':'Tarefa não encontrada ou nao deletada.'}, status=400)
        try: 
            tarefas = service.obter_tarefas_deletadas_por_id(tarefa_id)
        except:
            return JsonResponse({'error': 'Tarefa não encontrada ou nao deletada.'}, status=404)
        tarefas.delete()
        return JsonResponse({'message': 'Tarefa excluida com sucesso.'}, status=200)

class HistoricoTarefasView(APIView):
    service = TarefasServices()
    permission_classes = [OnlyAdminDELETE]
    queryset = service.obter_tarefas_deletadas()
    
    def get(self, request):
        historico = HistoricoTarefas.objects.all()
        serializer = HistoricoTarefasSerializer(historico, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)


class HistoricoTarefasEspecificosView(APIView):
    service = TarefasServices()
    permission_classes = [OnlyAdminDELETE]
    queryset = service.obter_tarefas_deletadas()
    
    def get(self, request, tarefa_id):
        service = TarefasServices()
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)
        try:
            historico = service.obter_historico_tarefas_por_id(tarefa_id)
        except Exception as e:
            return JsonResponse({'error': 'Histórico não encontrado.'}, status=404)
        
        serializer = HistoricoTarefasSerializer(historico, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
    def delete(self,request,tarefa_id):
        service = TarefasServices()
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)     
        try:
            historico = service.obter_historico_tarefas_por_id(tarefa_id)
        except Exception as e:
            return JsonResponse({'error': 'Histórico não encontrado.'}, status=404)
        historico.delete()
        return JsonResponse({'message': 'Histórico excluído com sucesso.'}, status=204)
    
    
class TarefasConcluidasEspecificasView(APIView):
    permission_classes = [OnlyAdminDELETE]
    
    
    def get(request,tarefa_id:int):
        service = TarefasServices()
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)     
        try:
            tarefa = service.obter_tarefa_concluida_por_id(tarefa_id)
        except:
            return JsonResponse({'error': 'Tarefa nao encontrada ou nao concluida.'}, status=404)
        
        serializer = TarefasSerializer(tarefa)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
        
    def put(request,tarefa_id:int):
        service = TarefasServices()
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)     
        try:
            tarefa = service.obter_tarefa_concluida_por_id(tarefa_id)
        except:
            return JsonResponse({'error': 'Tarefa nao encontrada ou nao concluida.'}, status=404)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Dados inválidos.'}, status=400)
        serializer = TarefasSerializer(tarefa, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=200)
        return JsonResponse(serializer.errors, status=400)
        
    def delete(request,tarefa_id:int):
        service = TarefasServices()
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)     
        try:
            tarefa = service.obter_tarefa_concluida_por_id(tarefa_id)   
        except Tarefas.DoesNotExist:
            return JsonResponse({'error': 'Tarefa nao encontrada ou nao concluida.'}, status=404)
        tarefa.delete()
        return JsonResponse({'message': 'Tarefa excluida com sucesso.'}, status=200)