from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from ..serializers import DocumentosSerializer, ArquivoModelSerializer, ArquivoTarefaSerializer
from .services import DocumentoService
from .permissions import OnlyAdminDELETE


class DocumentosViewSet(viewsets.ModelViewSet):
    service = DocumentoService()
    queryset = service.obter_queryset_documento()
    serializer_class = DocumentosSerializer
    permission_classes = [OnlyAdminDELETE]    
    
class ArquivoModelViewSet(viewsets.ModelViewSet):
    service = DocumentoService()
    queryset = service.obter_queryset_arquivos()
    serializer_class = ArquivoModelSerializer
    permission_classes = [OnlyAdminDELETE]


class ArquivoTarefaViewSet(viewsets.ModelViewSet):
    service = DocumentoService()
    queryset = service.obter_queryset_arquivos_tarefa()
    serializer_class = ArquivoTarefaSerializer
    permission_classes = [OnlyAdminDELETE]


class ArquivoModelClienteIdView(APIView):
    permission_classes = [OnlyAdminDELETE]


    def get(self, request, cliente):
        service = DocumentoService()
        try:
            arquivos = service.obter_arquivos_por_cliente(cliente_id=cliente)
        except None:
            return Response({'error': 'ArquivoModel nao encontrado.'}, status=404)
        serializer = ArquivoModelSerializer(arquivos, many=True)
        return Response(serializer.data)  

class ArquivoTarefaIdView(APIView):
    permission_classes = [OnlyAdminDELETE]

    def get(self, request, tarefa):
        service = DocumentoService()
        try:
            arquivos = service.obter_arquivo_tarefa_por_id(arquivo_id=tarefa)
        except None: # o service ou retorna um objeto ou None.
            return Response({'error': 'ArquivoModel nao encontrado.'}, status=404)
        serializer = ArquivoTarefaSerializer(arquivos, many=True)
        return Response(serializer.data) 
