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

class TarefasViewSet(viewsets.ModelViewSet):
    queryset = Tarefas.objects.all()
    serializer_class = TarefasSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

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
    def get(self, request, processo_id):
        if not processo_id:
            return JsonResponse({'error': 'ID do processo obrigatório.'}, status=400)
        try:
            tarefas = Tarefas.objects.filter(processoOrigemId=processo_id,deletada=False)  
        except:
            return JsonResponse({'error': 'Processo não encontrado.'})
        
        serializer = TarefasSerializer(tarefas, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
    
class TarefasDeletadasView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = Tarefas.objects.filter(deletada=True)
    
    def get(self, request):
        tarefas = Tarefas.objects.filter(deletada=True)
        serializer = TarefasSerializer(tarefas, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
    
class TarefasDeletadasEspecificasView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = Tarefas.objects.filter(deletada=True)
    
    def get(self, request, tarefa_id):
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)
        try:
            tarefa = Tarefas.objects.get(id=tarefa_id,deletada=True)  
        except:
            return JsonResponse({'error': 'Tarefa nao encontrada.'})
        
        serializer = TarefasSerializer(tarefa)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
    def patch(self,request,tarefa_id):
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
    
    def delete(self,request,tarefa_id):
        if not tarefa_id:
            return JsonResponse({'error':'Tarefa não encontrada ou nao deletada.'}, status=400)
        try: 
            tarefas = Tarefas.objects.get(id=tarefa_id,deletada = True)
        except Tarefas.DoesNotExist:
            return JsonResponse({'error': 'Tarefa não encontrada ou nao deletada.'}, status=404)
        tarefas.delete()
        return JsonResponse({'message': 'Tarefa excluida com sucesso.'}, status=200)


class HistoricoTarefasEspecificosView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = Tarefas.objects.filter(deletada=True)
    
    def get(self, request, tarefa_id):
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)
        try:
            historico = HistoricoTarefas.objects.filter(tarefaId=tarefa_id)  
        except HistoricoTarefas.DoesNotExist:
            return JsonResponse({'error': 'Histórico não encontrado.'}, status=404)
        
        serializer = HistoricoTarefasSerializer(historico, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    
    def delete(self,request,tarefa_id):
        if not tarefa_id:
            return JsonResponse({'error': 'ID da tarefa obrigatório.'}, status=400)     
        try:
            historico = HistoricoTarefas.objects.filter(tarefaId=tarefa_id)  
        except HistoricoTarefas.DoesNotExist:
            return JsonResponse({'error': 'Histórico não encontrado.'}, status=404)
        historico.delete()
        return JsonResponse({'message': 'Histórico excluído com sucesso.'}, status=204)
    