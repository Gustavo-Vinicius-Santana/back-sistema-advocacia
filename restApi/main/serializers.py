from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Cliente, Advogado, Processo,Tarefas,ClienteEspera

class ClienteSerializer(serializers.ModelSerializer):
    endereco = serializers.SerializerMethodField(method_name='get_endereco')
    class Meta:
        model = Cliente
        fields = ['id','nome','cpf','telefone','sexo','dataNascimento','nacionalidade','profissao','parceiro','inss','cep', 'numero', 'rua', 'estado','bairro', 'cidade', 'complemento','endereco','observacoes','foto']
    def get_endereco(self,obj):
        endereco = {
            'cep':obj.cep,
            'numero':obj.numero,
            'rua':obj.rua,
            'estado':obj.estado,
            'bairro':obj.bairro,
            'cidade':obj.cidade,
            'complemento':obj.complemento,
            }
        return endereco
    def validate(self,data):
        contrato = data.get('contrato')
        motivo = data.get('motivo')
        if contrato == False and(not motivo or motivo.strip() == "Sem motivo."):
            raise serializers.ValidationError({"motivo": "Se o contrato for False, o motivo deve ser preenchido."})
        return data
    

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
        fields = ['id','nome','telefone','observacao','IdAdvogado','cpf']
        
class AdvogadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advogado
        fields = ['id','nome','email','sexo','oab']
        
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
    dataContrato = serializers.DateTimeField(format="%d/%m/%Y")
    prazoContrato = serializers.DateTimeField(format="%d/%m/%Y") 
    advogadoCriadorNome = serializers.CharField(source='advogadoCriadorId.nome',read_only=True)
    class Meta:
        model = Processo
        fields = '__all__'


class TarefasSerializer(serializers.ModelSerializer):
    processoOrigemNumero = serializers.CharField(source='processoOrigemId.numeroProcesso',read_only=True)
    advogadoCriadorNome = serializers.CharField(source='advogadoCriadorId.nome',read_only=True)
    advogadoResponsavelNome = serializers.CharField(source='advogadoResponsavelId.nome',read_only=True)
    dataInicio = serializers.DateTimeField(format="%d/%m/%Y ")
    prazoFinal = serializers.DateTimeField(format="%d/%m/%Y ")
    class Meta:
        model = Tarefas
        fields = '__all__'
        
        
