from rest_framework import serializers
from .models import Cliente, Advogado, Processo,Tarefas

class ClienteSerializer(serializers.ModelSerializer):
    endereco = serializers.SerializerMethodField(method_name='get_endereco')
    class Meta:
        model = Cliente
        fields = ['id','nome','cpf','telefone','sexo','dataNascimento','nacionalidade','profissao','parceiro','inss','contrato','motivo','cep', 'numero', 'rua', 'estado', 'cidade', 'complemento','endereco','observacoes']
    def get_endereco(self,obj):
        endereco = {
            'cep':obj.cep,
            'numero':obj.numero,
            'rua':obj.rua,
            'estado':obj.estado,
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

class AdvogadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advogado
        fields = '__all__'
        
class AdvogadoResumidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advogado
        fields = ['id','nome']
        

class ProcesssosResumidoSerializer(serializers.ModelSerializer):
    advogadoCriadorNome = serializers.CharField(source='advogadoCriadorId.nome',read_only=True) 
    class Meta:
        model = Processo
        fields = ['id','advogadoCriadorId','advogadoCriadorNome']

class ProcessoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Processo
        fields = '__all__'


class TarefasSerializer(serializers.ModelSerializer):
    advogadoCriadorNome = serializers.CharField(source='AdvogadoCriadorId.nome',read_only=True)
    advogadoResponsavelNome = serializers.CharField(source='advogadoResponsavelId.nome',read_only=True)
    
    class Meta:
        model = Tarefas
        fields = '__all__'
        