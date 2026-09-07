from ...models import Tarefas,TipoTarefa,HistoricoTarefas
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db.models import Count, Q, Case, When, IntegerField


class TarefasServices:
    # Constantes de validação
    ALLOWED_ORDER_FIELDS = [
        'prazoFinal', '-prazoFinal',
        'dataInicio', '-dataInicio'
    ]

    def obter_queryset(self)-> Tarefas:
        return Tarefas.objects.all()
    
    def custom_queryset(self)->Tarefas:
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
        
    def list_services(self, request,queryset)->Tarefas:
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
                raise ValueError("Campo de filtro inválido.")
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
            raise ValueError("Parâmetro 'value' é obrigatório quando 'field' é fornecido.")
        elif not field and value:
            raise ValueError("Parâmetro 'field' é obrigatório quando 'value' é fornecido.")
        
        # NOVO: Filtro por ID do cliente
        if cliente_id is not None:
            try:
                cliente_id_int = int(cliente_id)
                queryset = queryset.filter(processoOrigemId__clienteId__id=cliente_id_int)
            except ValueError:
                raise ValueError("ID do cliente deve ser um número válido.")

        # Filtro por ID do advogado responsável
        if advogado_responsavel_id is not None:
            try:
                advogado_id = int(advogado_responsavel_id)
                queryset = queryset.filter(advogadoResponsavelId__id=advogado_id)
            except ValueError:
                raise ValueError("ID do advogado responsável deve ser um número válido.")

        # Filtro por ID do advogado criador
        if advogado_criador_id is not None:
            try:
                advogado_id = int(advogado_criador_id)
                queryset = queryset.filter(advogadoCriadorId__id=advogado_id)
            except ValueError:
                raise ValueError("ID do advogado criador deve ser um número válido.")

        # Filtro por ID do processo de origem
        if processo_origem_id is not None:
            try:
                processo_id = int(processo_origem_id)
                queryset = queryset.filter(processoOrigemId__id=processo_id)
            except ValueError:
                raise ValueError("ID do processo de origem deve ser um número válido.")

        # Filtro por concluida - somente se o parâmetro for fornecido
        if concluida is not None:
            if concluida.lower() in ['true', '1', 'yes', 'verdadeiro', 'sim']:
                queryset = queryset.filter(concluida=True)
            elif concluida.lower() in ['false', '0', 'no', 'falso', 'não', 'nao']:
                queryset = queryset.filter(concluida=False)
            else:
                raise ValueError("Valor inválido para 'concluida'. Use 'true' ou 'false'.")

        # Filtro por deletada - somente se o parâmetro for fornecido
        if deletada is not None:
            if deletada.lower() in ['true', '1', 'yes', 'verdadeiro', 'sim']:
                queryset = queryset.filter(deletada=True)
            elif deletada.lower() in ['false', '0', 'no', 'falso', 'não', 'nao']:
                queryset = queryset.filter(deletada=False)
            else:
                raise ValueError("Valor inválido para 'deletada'. Use 'true' ou 'false'.")

        # Filtro por status - somente se o parâmetro for fornecido
        if status is not None:
            valid_statuses = ['em aberto', 'atrasada', 'perto do prazo']
            if status not in valid_statuses:
                raise ValueError(f"Status inválido. Status válidos: {', '.join(valid_statuses)}")
            queryset = queryset.filter(status=status)

        # Filtro por urgente - somente se o parâmetro for fornecido
        if urgente is not None:
            if urgente.lower() in ['true', '1', 'yes', 'verdadeiro', 'sim']:
                queryset = queryset.filter(urgente=True)
            elif urgente.lower() in ['false', '0', 'no', 'falso', 'não', 'nao']:
                queryset = queryset.filter(urgente=False)
            else:
                raise ValueError("Valor inválido para 'urgente'. Use 'true' ou 'false'.")
        
        # Ordenação com hierarquia natural
        # Hierarquia: Atrasadas > Urgentes > Perto do prazo > Normais
        # As normais são ordenadas pelo campo order_by selecionado
        priority_order = Case(
            When(status='atrasada', then=1),
            When(urgente=True, then=2),
            When(status='perto do prazo', then=3),
            default=4,
            output_field=IntegerField()
        )

        if order_by:
            # Verifica se o campo de ordenação é permitido
            if order_by not in self.ALLOWED_ORDER_FIELDS:
                raise ValueError(f"Campo de ordenação inválido: {order_by}")
            # Ordena por prioridade primeiro, depois pelo campo selecionado
            queryset = queryset.annotate(priority=priority_order).order_by('priority', order_by)
        else:
            # Ordenação padrão: por prioridade e depois por data de criação (mais recente primeiro)
            queryset = queryset.annotate(priority=priority_order).order_by('priority', '-dataInicio')
        
       
        return queryset
    
    def obter_tipos_tarefas(self)-> TipoTarefa:
        return TipoTarefa.objects.all()
    
    
    def obter_tipo_tarefa_anotado(self)-> TipoTarefa:
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
    
    
    def criar_historico_tarefa(self, tarefa_id: int, data_Hora: str, advogado_nome: str, campos_mudados_formatados: str) -> bool:
        try:
            HistoricoTarefas.objects.create(
                tarefaId=tarefa_id,
                dataHora=data_Hora,
                acao=f'{data_Hora} - {advogado_nome} alterou o(s) campo(s): {campos_mudados_formatados}'
            )
            return True
        except Exception:
            return False
        
        
    def obter_tarefas_por_processo(self, processo_id: int)-> Tarefas:
        return Tarefas.objects.filter(
            processoOrigemId=processo_id,
            deletada=False
        )  # Inclui processo
        
        
    def obter_tarefas_deletadas(self)-> Tarefas:
        return Tarefas.objects.filter(deletada=True)
         
         

    def obter_tarefas_deletadas_por_id(self, tarefa_id: int)-> Tarefas:
            return Tarefas.objects.filter(id=tarefa_id, deletada=True)

    
    def obter_historico_tarefas_por_id(self, tarefa_id: int)-> HistoricoTarefas:
        return HistoricoTarefas.objects.filter(tarefaId=tarefa_id)
    
    def obter_tarefa_concluida_por_id(self, tarefa_id: int)-> Tarefas:
        return Tarefas.objects.get(id=tarefa_id,concluida = True)