from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import ClienteSerializer, AdvogadoSerializer, ProcessoSerializer
from .models import Cliente, Advogado, Processo



class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    
    
class AdvogadoViewSet(viewsets.ModelViewSet):
    queryset = Advogado.objects.all()
    serializer_class = AdvogadoSerializer
    permission_classes = [IsAuthenticated]
    
    
class ProcessoViewSet(viewsets.ModelViewSet):
    queryset = Processo.objects.all()
    serializer_class = ProcessoSerializer
    permission_classes = [IsAuthenticated]
    
    

