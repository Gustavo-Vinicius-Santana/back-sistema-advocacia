from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import *
class ClienteSerializer(serializers.ModelSerializer):
    endereco = serializers.SerializerMethodField(method_name='get_endereco')
    representanteNome = serializers.CharField(source='representante.nome', read_only=True)

    class Meta:
        model = Cliente
        fields = '__all__'

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
    class Meta:
        model = Parceiros
        fields = '__all__'
        
    def get_endereco(self,obj):
        endereco = {
            'numero':obj.numero,
            'rua':obj.rua,
            'estado':obj.estado,
            'bairro':obj.bairro,
            'cidade':obj.cidade,
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
    class Meta:
        model = Advogado
        fields = ['id','nome','telefone','email','foto','oab','is_active','is_staff','is_superuser','is_online','last_login']
        
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
    clienteNome = serializers.CharField(source='clienteId.nome',read_only=True)
    dataContrato = serializers.DateTimeField()
    advogadoCriadorNome = serializers.CharField(source='advogadoCriadorId.nome',read_only=True)
    grupoAcaoNome = serializers.CharField(source='grupoAcao.nome',read_only=True)
    faseNome = serializers.CharField(source='fase.nome',read_only=True)
    class Meta:
        model = Processo
        fields = '__all__'
        
        
class GrupoAcaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoAcao
        fields = '__all__'


class TipoAcaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAcao
        fields = '__all__'
        
        
class FaseProcessoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaseProcesso
        fields = '__all__'
        
        
class EtapaProcessoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtapaProcesso
        fields = '__all__'


class TarefasSerializer(serializers.ModelSerializer):
    processoOrigemNumero = serializers.CharField(source='processoOrigemId.numeroProcesso',read_only=True)
    advogadoCriadorNome = serializers.CharField(source='advogadoCriadorId.nome',read_only=True)
    advogadoResponsavelNome = serializers.CharField(source='advogadoResponsavelId.nome',read_only=True)
    tipoTarefaNome = serializers.CharField(source='tipoTarefa.nome',read_only=True)
    clienteNome = serializers.CharField(source='processoOrigemId.clienteId.nome',read_only=True)
    prazoFinal = serializers.DateTimeField(input_formats=['%Y-%m-%d'])
    dataInicio = serializers.DateTimeField(read_only=True)
    class Meta:
        model = Tarefas
        fields = '__all__'
        

class TipoTarefaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoTarefa
        fields = '__all__'


        
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