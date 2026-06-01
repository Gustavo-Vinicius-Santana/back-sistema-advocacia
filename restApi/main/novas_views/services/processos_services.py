from ...models import Processo
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta, date, datetime


class ProcessoService:
    # Constantes de validação
    ALLOWED_FILTER_FIELDS = [
        'numeroProcesso', 'fase', 'status', 'clienteId', 'advogadoCriadorId',
        'dataContrato', 'titulo', 'classificacao', 'prioritario', 'concluido',
        'total_tarefas', 'tarefas_em_aberto', 'tarefas_atrasadas',
        'tarefas_concluidas', 'tarefas_urgentes', 'tarefas_perto_prazo'
    ]

    ALLOWED_ORDER_FIELDS = [
        'id', 'numeroProcesso', 'titulo', 'dataContrato', 'prioritario',
        'clienteId__nome', '-clienteId__nome',
        'advogadoCriadorId__nome', '-advogadoCriadorId__nome',
        'fase', '-fase', 'fase__nome', '-fase__nome',
        'status', '-status',
        'total_tarefas', '-total_tarefas',
        'tarefas_em_aberto', '-tarefas_em_aberto',
        'tarefas_atrasadas', '-tarefas_atrasadas',
        'tarefas_concluidas', '-tarefas_concluidas',
        'tarefas_urgentes', '-tarefas_urgentes',
        'tarefas_perto_prazo', '-tarefas_perto_prazo'
    ]

    VALID_STATUSES = ['ativo', 'arquivado']
    VALID_PERIODOS = ['hoje', 'semana', 'mes', 'ano']

    def __init__(self) -> None:
        pass

    def get_queryset_anotado(self):
        """
        Retorna queryset base com todas as anotações de tarefas.
        Encapsula a lógica de annotate que estava no get_queryset da view.
        """
        return Processo.objects.annotate(
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

    def filtrar_por_cliente_id(self, queryset, cliente_id_filter):
        """Filtra processos por ID do cliente"""
        if cliente_id_filter:
            try:
                cliente_id = int(cliente_id_filter)
                return queryset.filter(clienteId__id=cliente_id)
            except (ValueError, TypeError):
                raise ValueError("ID do cliente deve ser um número inteiro válido")
        return queryset

    def filtrar_por_status(self, queryset, status_filter):
        """Filtra processos por status"""
        if status_filter:
            status_list = [s.strip() for s in status_filter.split(',')]
            filtered_statuses = [s for s in status_list if s in self.VALID_STATUSES]

            if filtered_statuses:
                if len(filtered_statuses) == 1:
                    return queryset.filter(status=filtered_statuses[0])
                else:
                    return queryset.filter(status__in=filtered_statuses)
            else:
                raise ValueError("Status inválido. Use: 'ativo', 'arquivado' ou 'ativo,arquivado'")
        return queryset

    def filtrar_por_concluido(self, queryset, concluido_filter):
        """Filtra processos por status de conclusão"""
        if concluido_filter is not None:
            valores_verdadeiros = ['true', '1', 'yes', 'sim', 'verdadeiro']
            valores_falsos = ['false', '0', 'no', 'não', 'nao', 'falso']

            if concluido_filter.lower() in valores_verdadeiros:
                return queryset.filter(concluido=True)
            elif concluido_filter.lower() in valores_falsos:
                return queryset.filter(concluido=False)
            else:
                raise ValueError("Valor inválido para 'concluido'. Use: 'true' para concluídos ou 'false' para não concluídos")
        return queryset

    def filtrar_por_campo_especifico(self, queryset, field, value):
        """Filtra processos por campo específico e valor"""
        if field not in self.ALLOWED_FILTER_FIELDS:
            raise ValueError(f"Campo de filtro inválido: {field}")

        # Campos de texto simples
        if field in ['numeroProcesso', 'fase', 'status', 'titulo', 'classificacao']:
            return queryset.filter(**{f"{field}__icontains": value})

        # Campos de relacionamento
        elif field == 'clienteId':
            return queryset.filter(clienteId__nome__icontains=value)

        elif field == 'advogadoCriadorId':
            return queryset.filter(advogadoCriadorId__nome__icontains=value)

        # Campo de data específica
        elif field == 'dataContrato':
            try:
                data_valor = datetime.fromisoformat(value.replace('Z', '+00:00')) if 'T' in value else date.fromisoformat(value)
                data_inicio_dia = timezone.make_aware(datetime.combine(data_valor, datetime.min.time()))
                data_fim_dia = timezone.make_aware(datetime.combine(data_valor, datetime.max.time()))
                return queryset.filter(dataContrato__range=[data_inicio_dia, data_fim_dia])
            except (ValueError, TypeError):
                raise ValueError("Formato de data inválido. Use YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS")

        # Campos booleanos
        elif field == 'prioritario':
            valores_verdadeiros = ['true', '1', 'yes', 'sim']
            valores_falsos = ['false', '0', 'no', 'não']
            if value.lower() in valores_verdadeiros:
                return queryset.filter(prioritario=True)
            elif value.lower() in valores_falsos:
                return queryset.filter(prioritario=False)
            else:
                raise ValueError("Valor inválido para 'prioritario'. Use: 'true' ou 'false'")

        elif field == 'concluido':
            valores_verdadeiros = ['true', '1', 'yes', 'sim']
            valores_falsos = ['false', '0', 'no', 'não']
            if value.lower() in valores_verdadeiros:
                return queryset.filter(concluido=True)
            elif value.lower() in valores_falsos:
                return queryset.filter(concluido=False)
            else:
                raise ValueError("Valor inválido para 'concluido'. Use: 'true' ou 'false'")

        # Campos de tarefas (numéricos)
        elif field == 'total_tarefas':
            try:
                valor = int(value)
                return queryset.filter(total_tarefas=valor)
            except (ValueError, TypeError):
                raise ValueError("total_tarefas deve ser um número inteiro válido")

        elif field in ['tarefas_em_aberto', 'tarefas_atrasadas', 'tarefas_concluidas', 'tarefas_urgentes', 'tarefas_perto_prazo']:
            try:
                valor = int(value)
                if valor > 0:
                    return queryset.filter(**{f"{field}__gte": valor})
                else:
                    return queryset.filter(**{field: 0})
            except (ValueError, TypeError):
                raise ValueError(f"{field} deve ser um número inteiro válido")

        return queryset

    def filtrar_por_periodo(self, queryset, periodo):
        """Filtra processos por período específico"""
        if periodo not in self.VALID_PERIODOS:
            raise ValueError("Período inválido. Use: 'hoje', 'semana', 'mes' ou 'ano'")

        hoje = timezone.now().date()

        if periodo == 'hoje':
            data_inicio = timezone.make_aware(datetime.combine(hoje, datetime.min.time()))
            data_fim = timezone.make_aware(datetime.combine(hoje, datetime.max.time()))

        elif periodo == 'semana':
            inicio_semana = hoje - timedelta(days=hoje.weekday())  # Segunda-feira
            fim_semana = inicio_semana + timedelta(days=6)  # Domingo
            data_inicio = timezone.make_aware(datetime.combine(inicio_semana, datetime.min.time()))
            data_fim = timezone.make_aware(datetime.combine(fim_semana, datetime.max.time()))

        elif periodo == 'mes':
            data_inicio = timezone.make_aware(datetime(hoje.year, hoje.month, 1, 0, 0, 0))
            if hoje.month == 12:
                data_fim = timezone.make_aware(datetime(hoje.year + 1, 1, 1, 0, 0, 0)) - timedelta(seconds=1)
            else:
                data_fim = timezone.make_aware(datetime(hoje.year, hoje.month + 1, 1, 0, 0, 0)) - timedelta(seconds=1)

        elif periodo == 'ano':
            data_inicio = timezone.make_aware(datetime(hoje.year, 1, 1, 0, 0, 0))
            data_fim = timezone.make_aware(datetime(hoje.year, 12, 31, 23, 59, 59))

        return queryset.filter(dataContrato__range=[data_inicio, data_fim])

    def filtrar_por_intervalo_data(self, queryset, data_inicio, data_fim):
        """Filtra processos por intervalo de datas específico"""
        try:
            if data_inicio:
                data_inicio_valor = datetime.fromisoformat(data_inicio.replace('Z', '+00:00')) if 'T' in data_inicio else date.fromisoformat(data_inicio)
                data_inicio_dt = timezone.make_aware(datetime.combine(data_inicio_valor, datetime.min.time()))
                queryset = queryset.filter(dataContrato__gte=data_inicio_dt)

            if data_fim:
                data_fim_valor = datetime.fromisoformat(data_fim.replace('Z', '+00:00')) if 'T' in data_fim else date.fromisoformat(data_fim)
                data_fim_dt = timezone.make_aware(datetime.combine(data_fim_valor, datetime.max.time()))
                queryset = queryset.filter(dataContrato__lte=data_fim_dt)

        except (ValueError, TypeError):
            raise ValueError("Formato de data inválido. Use YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS")

        return queryset

    def aplicar_ordenacao(self, queryset, order_by):
        """Aplica ordenação ao queryset"""
        if not order_by:
            return queryset.order_by('-prioritario', 'dataContrato')

        if order_by not in self.ALLOWED_ORDER_FIELDS:
            raise ValueError(f"Campo de ordenação inválido: {order_by}")

        return queryset.order_by(order_by)

    def filtrar_e_ordenar_completos(self, cliente_id=None, status=None, concluido=None,
                                   field=None, value=None, periodo=None,
                                   data_inicio=None, data_fim=None, order_by=None):
        """
        Método principal que aplica todos os filtros e ordenação.
        Encapsula TODA a lógica complexa que estava na view.
        """
        queryset = self.get_queryset_anotado()

        # Aplicar filtros em sequência
        try:
            queryset = self.filtrar_por_cliente_id(queryset, cliente_id)
            queryset = self.filtrar_por_status(queryset, status)
            queryset = self.filtrar_por_concluido(queryset, concluido)

            if field and value:
                queryset = self.filtrar_por_campo_especifico(queryset, field, value)

            if periodo:
                queryset = self.filtrar_por_periodo(queryset, periodo)
            elif data_inicio or data_fim:
                queryset = self.filtrar_por_intervalo_data(queryset, data_inicio, data_fim)

            queryset = self.aplicar_ordenacao(queryset, order_by)

        except ValueError as e:
            raise ValueError(str(e))

        return queryset