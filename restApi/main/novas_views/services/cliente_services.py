from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import datetime
from main.models import Cliente, ClienteEspera

class ClienteService:
    ALLOWED_FIELDS = ['nome', 'cpf', 'telefone', 'inss', 'parceiro']
    ALLOWED_ORDER_FIELDS = [
        'id', 'nome', 'cpf', 'telefone', 'inss', 'parceiro',
        'prioridade', '-prioridade'
    ]
    
    def __init__(self) -> None:
        pass
    
    def get_queryset_anotado(self) -> 'QuerySet[Cliente]':
        data_atual = timezone.now().date()
        data65 = data_atual - relativedelta(years=65)
        data_inicio = data65 - relativedelta(days=5)
        data_fim = data65 + relativedelta(days=5)

        return Cliente.objects.annotate(
            prioridade=Case(
                When(
                    dataNascimento__range=(data_inicio, data_fim),
                    then=Value(1)
                ),
                default=Value(0),
                output_field=IntegerField()
            ),
            processos_ativos_count=Count(
                'processo',
                filter=Q(processo__status='ativo')
            ),
            processos_arquivados_count=Count(
                'processo',
                filter=Q(processo__status='arquivado')
            ),
            processos_urgentes_count=Count(
                'processo',
                filter=Q(processo__status='ativo') & 
                       Q(processo__prioritario=True)
            ),
            processos_total_count=Count('processo')
        ).order_by('-prioridade', 'id')
    
    def filtrar_e_ordenar(self, field=None, value=None, order_by=None, contrato=None):
        queryset = self.get_queryset_anotado()
        
        if contrato is not None:
            if isinstance(contrato, str):
                if contrato.lower() in ['true', '1', 'yes']:
                    queryset = queryset.filter(contrato=True)
                elif contrato.lower() in ['false', '0', 'no']:
                    queryset = queryset.filter(contrato=False)
                else:
                    raise ValueError("Valor inválido para o parâmetro 'contrato'. Use 'true' ou 'false'.")
            else:
                queryset = queryset.filter(contrato=contrato)
        
        if field and value:
            if field not in self.ALLOWED_FIELDS:
                raise ValueError(f"Campo de filtro inválido: {field}")
            if field in ['nome', 'cpf', 'telefone', 'inss']:
                queryset = queryset.filter(**{f"{field}__icontains": value})
            elif field == 'parceiro':
                queryset = queryset.filter(parceiro__nome__icontains=value)
        
        if order_by:
            if order_by not in self.ALLOWED_ORDER_FIELDS:
                raise ValueError(f"Campo de ordenação inválido: {order_by}")
            if order_by == 'parceiro':
                queryset = queryset.order_by('parceiro__nome')
            else:
                queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('-prioridade', 'id')
        
        return queryset
    
    def calcular_dias_para_65_anos(self, data_nascimento):
        if not data_nascimento:
            return None
        
        data_atual = timezone.now().date()
        data_65 = data_nascimento + relativedelta(years=65)
        return (data_65 - data_atual).days
    
    def obter_clientes_sem_contrato(self, field=None, value=None, order_by=None):
        allowed_field = ['nome', 'dataNascimento', 'sexo', 'email', 'telefone']
        
        if field and value:
            if field not in allowed_field:
                raise ValueError(f'O campo "{field}" não é permitido para busca.')
            queryset = Cliente.objects.filter(
                contrato=False
            ).filter(**{f"{field}__icontains": value})
        else:
            queryset = Cliente.objects.filter(contrato=False)
        
        data_atual = timezone.now().date()
        data65 = data_atual - relativedelta(years=65)
        data_inicio = data65 - relativedelta(days=5)
        data_fim = data65 + relativedelta(days=5)
        
        queryset = queryset.annotate(
            prioridade=Case(
                When(
                    dataNascimento__range=(data_inicio, data_fim),
                    then=Value(1)
                ),
                default=Value(0),
                output_field=IntegerField()
            )
        )
        
        if order_by:
            queryset = queryset.order_by('-prioridade', order_by)
        else:
            queryset = queryset.order_by('-prioridade', 'id')
        
        return queryset
    
    def buscar_por_campo(self, field, value, order_by=None):
        allowed_field = ['nome', 'cpf', 'telefone', 'inss', 'parceiro']
        
        if not field or not value:
            raise ValueError("Os campos 'field' e 'value' são obrigatórios.")
        
        if field not in allowed_field:
            raise ValueError(f"O campo '{field}' não é permitido para busca.")
        
        if field == 'parceiro':
            queryset = Cliente.objects.filter(parceiro__nome__icontains=value)
        else:
            queryset = Cliente.objects.filter(**{f"{field}__icontains": value})
        
        if order_by:
            if order_by == 'parceiro':
                queryset = queryset.order_by('parceiro__nome')
            else:
                queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('id')
        
        return queryset
    
    def obter_clientes_espera_por_advogado(self, advogado_id):
        if not advogado_id:
            raise ValueError("O ID do advogado é obrigatório.")
        
        clientes_espera = ClienteEspera.objects.filter(IdAdvogado=advogado_id)
        return clientes_espera