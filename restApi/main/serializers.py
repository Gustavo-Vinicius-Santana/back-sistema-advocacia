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

class ProcessoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Processo
        fields = '__all__'


class TarefasSerializer(serializers.ModelSerializer):
    criador_nome = serializers.CharField(source='criador.nome',read_only=True)
    advogadoResponsavel_nome = serializers.CharField(source='advogadoResponsavel.nome',read_only=True)
    
    class Meta:
        model = Tarefas
        fields = '__all__'
        