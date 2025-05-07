from rest_framework import serializers
from .models import Cliente, Advogado, Processo,Tarefas

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
    
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
    advogadoResponsavelNome = serializers.CharField(source='advogadoResponsavelId.nome',read_only=True) 
    class Meta:
        model = Processo
        fields = ['id','advogadoResponsavelId','advogadoResponsavelNome']

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
        