from django.conf import settings
from django.db.models import Count, Q
from ...models import Advogado, Tarefas, Processo

class AdvogadoService:
    # Constantes de validação
    ALLOWED_FIELDS = ['nome', 'email', 'telefone', 'oab']
    ALLOWED_ORDER_FIELDS = [
        'id', 'nome', 'email', 'telefone', 'oab',
        'tarefas_criadas', '-tarefas_criadas',
        'tarefas_responsavel', '-tarefas_responsavel'
    ]
    
    def __init__(self) -> None:
        self.chave_esperada = str(getattr(settings,'API_SECRET_KEY'))

    def validate_chave_login(self, chave: str) -> bool:
        """Valida chave de API para registro de advogados"""
        if chave == self.chave_esperada:
            return True
        return False
    
    def get_queryset_anotado(self) -> 'QuerySet[Advogado]':
        """
        Retorna queryset base com anotações de contagem de tarefas.
        Encapsula a lógica de annotate que estava no get_queryset da view.
        """
        return Advogado.objects.annotate(
            tarefas_criadas=Count(
                'advogadoCriador__id',
                distinct=True,
                filter=Q(advogadoCriador__deletada=False)
            ),
            tarefas_responsavel=Count(
                'advogadoResponsavel__id',
                distinct=True,
                filter=Q(advogadoResponsavel__deletada=False)
            )
        )
    
    def filtrar_e_ordenar(self, field=None, value=None, order_by=None):
        """
        Filtra e ordena advogados com base nos parâmetros.
        
        Args:
            field: campo para filtro ('nome', 'email', etc)
            value: valor para filtro
            order_by: campo para ordenação
            
        Returns:
            QuerySet filtrado e ordenado
            
        Raises:
            ValueError: se field ou order_by forem inválidos
        """
        queryset = self.get_queryset_anotado()
        
        # Aplicar filtro
        if field and value:
            if field not in self.ALLOWED_FIELDS:
                raise ValueError(f"Campo de filtro inválido: {field}")
            queryset = queryset.filter(**{f"{field}__icontains": value})
        
        # Aplicar ordenação
        if order_by:
            if order_by not in self.ALLOWED_ORDER_FIELDS:
                raise ValueError(f"Campo de ordenação inválido: {order_by}")
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('id')
        
        return queryset
    
    def obter_dashboard(self, advogado_id: int) -> dict:
        """
        Retorna dados do dashboard para um advogado específico.
        Encapsula toda a lógica que estava em AdvogadosDashboardView.
        """
        try:
            advogado = Advogado.objects.get(id=advogado_id)
            
            # Tarefas do advogado
            tarefas = Tarefas.objects.filter(advogadoResponsavelId=advogado.id)
            tarefas_concluidas = tarefas.filter(concluida=True).count()
            tarefas_pendentes = tarefas.filter(concluida=False).count()
            
            # Processos
            processos_ativos = Processo.objects.filter(
                advogadoCriadorId=advogado.id,
                status='ativo'
            ).exclude(concluido=True).count()
            
            processos_concluidos = Processo.objects.filter(
                advogadoCriadorId=advogado.id,
                concluido=True
            ).count()
            
            return {
                'tarefasConcluidas': tarefas_concluidas,
                'tarefasPendentes': tarefas_pendentes,
                'processosAtivos': processos_ativos,
                'processosConcluidos': processos_concluidos,
            }
        except Advogado.DoesNotExist:
            raise ValueError(f"Advogado com ID {advogado_id} não encontrado")
    
    def atualizar_status_online(self, advogado_id: int, is_online: bool) -> Advogado:
        """
        Atualiza o status online de um advogado.
        Encapsula a lógica de logout/login.
        """
        try:
            advogado = Advogado.objects.get(id=advogado_id)
            advogado.is_online = is_online
            advogado.save()
            return advogado
        except Advogado.DoesNotExist:
            raise ValueError(f"Advogado com ID {advogado_id} não encontrado")
    
    def registrar_advogado(self, nome: str, email: str, telefone: str = None, 
                          oab: str = None, foto: str = None, is_staff: bool = False,password: str = None) -> Advogado:
        """
        Cria um novo advogado com validações básicas.
        Encapsula a lógica de registro.
        """
        if not nome or not email:
            raise ValueError("Nome e email são obrigatórios")
        
        if password and len(password) < 12:
            raise ValueError("A senha deve ter no mínimo 12 caracteres")
        
        if Advogado.objects.filter(email=email).exists():
            raise ValueError("Email já está registrado")
        
        advogado = Advogado.objects.create(
            nome=nome,
            telefone=telefone,
            email=email,
            oab=oab,
            foto=foto,
            is_staff=is_staff
        )
        
        if password:
            advogado.set_password(password)
            advogado.save()
        
        return advogado
        
    