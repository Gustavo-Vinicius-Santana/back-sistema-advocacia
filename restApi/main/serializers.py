from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import *
class ClienteSerializer(serializers.ModelSerializer):
    endereco = serializers.SerializerMethodField(method_name='get_endereco')
    representanteNome = serializers.CharField(source='representante.nome', read_only=True)
    parceiroNome = serializers.CharField(source='parceiro.nome', read_only=True)
    dias_para_65 = serializers.IntegerField(read_only=True)
    
    # Adicione os campos para contar processos nas diferentes categorias
    processos_ativos_count = serializers.IntegerField(read_only=True)
    processos_arquivados_count = serializers.IntegerField(read_only=True)
    processos_urgentes_count = serializers.IntegerField(read_only=True)
    processos_total_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cliente
        fields = '__all__'
        # Ou se preferir especificar os campos explicitamente:
        # fields = [
        #     'id', 'nome', 'cpf', 'telefone', 'dataNascimento', 
        #     'processos_ativos_count', 'processos_arquivados_count',
        #     'processos_urgentes_count', 'processos_total_count',
        #     ... outros campos
        # ]

    def get_endereco(self, obj):
        endereco = {
            'cep': obj.cep,
            'numero': obj.numero,
            'rua': obj.rua,
            'estado': obj.estado,
            'bairro': obj.bairro,
            'cidade': obj.cidade,
            'complemento': obj.complemento,
        }
        return endereco
    """def validate(self,data):
        contrato = data.get('contrato')
        motivo = data.get('motivo')
        if contrato == False and(not motivo or motivo.strip() == "Sem motivo."):
            raise serializers.ValidationError({"motivo": "Se o contrato for False, o motivo deve ser preenchido."})
        return data"""
    

class RepresentanteSerializer(serializers.ModelSerializer):
    endereco = serializers.SerializerMethodField(method_name='get_endereco')
    cliente_info = serializers.SerializerMethodField(method_name='get_clientes_info')
    class Meta:
        model = Representante
        fields = '__all__'

    def get_endereco(self,obj):
        endereco = {
            'cep':obj.cep,
            'numero':obj.numero,
            'rua':obj.rua,
            'estado':obj.estado,
            'bairro':obj.bairro,
            'cidade':obj.cidade,
            'complemento':obj.complemento
            }
        return endereco
    
    def get_clientes_info(self,obj):
        if obj.cliente:
            return {
                'id': obj.cliente.id,
                'nome': obj.cliente.nome,
            }
        
        
        
class ParceirosSerializer(serializers.ModelSerializer):
    endereco = serializers.SerializerMethodField(method_name='get_endereco')
    total_clientes = serializers.IntegerField(read_only=True)  # Campo do annotate
    
    class Meta:
        model = Parceiros
        fields = '__all__'
        extra_fields = ['endereco', 'total_clientes']
        
    def get_endereco(self, obj):
        endereco = {
            'numero': obj.numero,
            'rua': obj.rua,
            'estado': obj.estado,
            'bairro': obj.bairro,
            'cidade': obj.cidade,
        }
        return endereco

class EscritoriosSerializer(serializers.ModelSerializer):
    endereco = serializers.SerializerMethodField(method_name='get_endereco')
    class Meta:
        model = Escritorios
        fields = '__all__'
    def get_endereco(self,obj):
        endereco = {
            'cep':obj.cep,
            'numero':obj.numero,
            'rua':obj.rua,
            'estado':obj.estado,
            'complemento':obj.complemento,
            'bairro':obj.bairro,
            'cidade':obj.cidade,
            }
        return endereco

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Adiciona etapas customizadas ao login
        data = super().validate(attrs)
        user = self.user
        if user.is_active:
            user.is_online = True
            user.save()
        return data
    
class ClienteEsperaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClienteEspera
        fields = '__all__'
        
        
        
class AdvogadoSerializer(serializers.ModelSerializer):
    tarefas_criadas = serializers.IntegerField(read_only=True)
    tarefas_responsavel = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Advogado
        fields = [
            'id', 'nome', 'telefone', 'email', 'foto', 'oab',
            'is_active', 'is_staff', 'is_superuser', 'is_online', 'last_login',
            'tarefas_criadas', 'tarefas_responsavel'
        ]
        
class AdvogadoResumidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advogado
        fields = ['id','nome']
        

class ProcesssosResumidoSerializer(serializers.ModelSerializer):
    advogadoCriadorNome = serializers.CharField(source='advogadoCriadorId.nome',read_only=True) 
    cliente = serializers.CharField(source='clienteId.nome',read_only=True)
    
    class Meta:
        model = Processo
        fields = ['id','advogadoCriadorId','advogadoCriadorNome','cliente']

class ProcessoSerializer(serializers.ModelSerializer):
    clienteNome = serializers.CharField(source='clienteId.nome', read_only=True)
    dataContrato = serializers.DateTimeField()
    advogadoCriadorNome = serializers.CharField(source='advogadoCriadorId.nome', read_only=True)
    grupoAcaoNome = serializers.CharField(source='grupoAcao.nome', read_only=True)
    faseNome = serializers.CharField(source='fase.nome', read_only=True)
    
    # Adicione estes campos explicitamente
    total_tarefas = serializers.IntegerField(read_only=True, required=False)
    tarefas_em_aberto = serializers.IntegerField(read_only=True, required=False)
    tarefas_atrasadas = serializers.IntegerField(read_only=True, required=False)
    tarefas_concluidas = serializers.IntegerField(read_only=True, required=False)
    tarefas_urgentes = serializers.IntegerField(read_only=True, required=False)
    tarefas_perto_prazo = serializers.IntegerField(read_only=True, required=False)
    
    class Meta:
        model = Processo
        fields = '__all__'
        
        
class GrupoAcaoSerializer(serializers.ModelSerializer):
    total_processos = serializers.IntegerField(read_only=True)
    arquivados = serializers.IntegerField(read_only=True)
    concluidos = serializers.IntegerField(read_only=True)
    pendentes = serializers.IntegerField(read_only=True)
    urgentes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = GrupoAcao
        fields = [
            'id', 'nome', 'total_processos', 'arquivados', 
            'concluidos', 'pendentes', 'urgentes'
        ]


class TipoAcaoSerializer(serializers.ModelSerializer):
    total_processos = serializers.IntegerField(read_only=True)
    arquivados = serializers.IntegerField(read_only=True)
    concluidos = serializers.IntegerField(read_only=True)
    pendentes = serializers.IntegerField(read_only=True)
    urgentes = serializers.IntegerField(read_only=True)
    grupo_acao_nome = serializers.CharField(source='grupoAcao.nome', read_only=True)
    
    class Meta:
        model = TipoAcao
        fields = [
            'id', 'nome', 'grupoAcao', 'grupo_acao_nome', 'total_processos', 
            'arquivados', 'concluidos', 'pendentes', 'urgentes'
        ]
        
        
class FaseProcessoSerializer(serializers.ModelSerializer):
    total_processos = serializers.IntegerField(read_only=True)
    arquivados = serializers.IntegerField(read_only=True)
    concluidos = serializers.IntegerField(read_only=True)
    pendentes = serializers.IntegerField(read_only=True)
    urgentes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = FaseProcesso
        fields = [
            'id', 'nome', 'total_processos', 'arquivados',
            'concluidos', 'pendentes', 'urgentes'
        ]
        
        
class EtapaProcessoSerializer(serializers.ModelSerializer):
    faseProcesso_nome = serializers.CharField(source='faseProcesso.nome', read_only=True)
    total_processos = serializers.IntegerField(read_only=True)
    arquivados = serializers.IntegerField(read_only=True)
    concluidos = serializers.IntegerField(read_only=True)
    pendentes = serializers.IntegerField(read_only=True)
    urgentes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = EtapaProcesso
        fields = [
            'id', 'nome', 'faseProcesso', 'faseProcesso_nome',
            'total_processos', 'arquivados', 'concluidos',
            'pendentes', 'urgentes'
        ]


class TarefasSerializer(serializers.ModelSerializer):
    processoOrigemNumero = serializers.CharField(source='processoOrigemId.numeroProcesso', read_only=True)
    advogadoCriadorNome = serializers.CharField(source='advogadoCriadorId.nome', read_only=True)
    advogadoResponsavelNome = serializers.CharField(source='advogadoResponsavelId.nome', read_only=True)
    tipoTarefaNome = serializers.CharField(source='tipoTarefa.nome', read_only=True)
    clienteNome = serializers.CharField(source='processoOrigemId.clienteId.nome', read_only=True)
    # NOVO: Adiciona o ID do cliente
    clienteId = serializers.SerializerMethodField()
    prazoFinal = serializers.DateTimeField(input_formats=['%Y-%m-%d'])
    dataInicio = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Tarefas
        fields = '__all__'
    
    def get_clienteId(self, obj):
        # Método seguro para obter o ID do cliente
        # Acessa através da relação: Tarefa → Processo → Cliente
        try:
            # Verifica se existe o processo
            if obj.processoOrigemId:
                # Verifica se existe o cliente no processo
                if hasattr(obj.processoOrigemId, 'clienteId') and obj.processoOrigemId.clienteId:
                    return obj.processoOrigemId.clienteId.id
        except AttributeError:
            # Se houver qualquer erro de atributo, retorna None
            pass
        return None
        

class TipoTarefaSerializer(serializers.ModelSerializer):
    # Campos calculados que serão populados via annotate
    total_tarefas = serializers.IntegerField(read_only=True)
    concluidas = serializers.IntegerField(read_only=True)
    pendentes = serializers.IntegerField(read_only=True)
    pendentes_em_aberto = serializers.IntegerField(read_only=True)
    pendentes_atrasadas = serializers.IntegerField(read_only=True)
    pendentes_perto_prazo = serializers.IntegerField(read_only=True)
    pendentes_urgentes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = TipoTarefa
        fields = [
            'id', 'nome', 
            'total_tarefas', 'concluidas', 'pendentes',
            'pendentes_em_aberto', 'pendentes_atrasadas', 
            'pendentes_perto_prazo', 'pendentes_urgentes'
        ]
    
    def to_representation(self, instance):
        # Chama o método padrão primeiro
        data = super().to_representation(instance)
        
        # Extrai os valores
        total_tarefas = data.pop('total_tarefas')
        concluidas = data.pop('concluidas')
        pendentes = data.pop('pendentes')
        
        # Cria a nova estrutura organizada
        response_data = {
            'id': data['id'],
            'nome': data['nome'],
            'estatisticas': {
                'total': total_tarefas,
                'concluidas': {
                    'total': concluidas,
                    # Se quiser adicionar percentual
                    'percentual': f"{(concluidas / total_tarefas * 100):.1f}%" if total_tarefas > 0 else "0%"
                },
                'pendentes': {
                    'total': pendentes,
                    'detalhes': {
                        'em_aberto': data.pop('pendentes_em_aberto'),
                        'atrasadas': data.pop('pendentes_atrasadas'),
                        'perto_do_prazo': data.pop('pendentes_perto_prazo'),
                        'urgentes': data.pop('pendentes_urgentes')
                    },
                    # Se quiser adicionar percentual
                    'percentual': f"{(pendentes / total_tarefas * 100):.1f}%" if total_tarefas > 0 else "0%"
                }
            }
        }
        
        return response_data


        
class HistoricoTarefasSerializer(serializers.ModelSerializer):
    tarefaId = serializers.IntegerField(source='tarefaId.id',read_only=True)
    dataHora = serializers.DateTimeField(read_only=True,format="%Y-%m-%d %H:%M")
    acao = serializers.CharField(read_only=True)
    
    class Meta:
        model = Tarefas
        fields = ['tarefaId','dataHora','acao']
        read_only_fields = ['tarefaId','dataHora']
        

class DocumentosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documentos
        fields = '__all__'
        

class ArquivoModelSerializer(serializers.ModelSerializer):
    clienteNome = serializers.CharField(source='cliente_id.nome', read_only=True)
    class Meta:
        model = ArquivoModel
        fields = '__all__'
        
        
        
class ArquivoTarefaSerializer(serializers.ModelSerializer):
    tarefaNome = serializers.CharField(source='tarefa_id.nome', read_only=True)
    class Meta:
        model = ArquivoTarefa
        fields = '__all__'

class GenericSelectSerializer(serializers.Serializer):
    """
    Serializer dinâmico para selects - retorna {value, label}
    """
    value = serializers.IntegerField(source='id', read_only=True)
    label = serializers.SerializerMethodField()
    
    class Meta:
        fields = ['value', 'label']
    
    def get_label(self, obj):
        """
        Obtém o texto para o label baseado nos campos disponíveis
        """
        # Ordem de preferência para o label
        if hasattr(obj, 'nome'):
            return obj.nome
        elif hasattr(obj, 'name'):
            return obj.name
        elif hasattr(obj, 'razao_social'):
            return obj.razao_social
        elif hasattr(obj, 'titulo'):
            return obj.titulo
        elif hasattr(obj, 'descricao'):
            return obj.descricao
        else:
            return str(obj)
    
    def to_representation(self, instance):
        """
        Formata a resposta como {value, label}
        """
        return {
            'value': instance.id,
            'label': self.get_label(instance)
        }