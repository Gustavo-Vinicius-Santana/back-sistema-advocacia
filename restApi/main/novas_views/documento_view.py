

class DocumentosViewSet(viewsets.ModelViewSet):
    queryset = Documentos.objects.all()
    serializer_class = DocumentosSerializer
    permission_classes = [IsAuthenticated]    
    
class ArquivoModelViewSet(viewsets.ModelViewSet):
    queryset = ArquivoModel.objects.all()
    serializer_class = ArquivoModelSerializer
    permission_classes = [IsAuthenticated]


class ArquivoTarefaViewSet(viewsets.ModelViewSet):
    queryset = ArquivoTarefa.objects.all()
    serializer_class = ArquivoTarefaSerializer
    permission_classes = [IsAuthenticated]
  

class ArquivoModelClienteIdView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, cliente):
        try:
            arquivos = ArquivoModel.objects.filter(cliente_id=cliente)
        except ArquivoModel.DoesNotExist:
            return Response({'error': 'ArquivoModel nao encontrado.'}, status=404)
        serializer = ArquivoModelSerializer(arquivos, many=True)
        return Response(serializer.data)  

class ArquivoTarefaIdView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, tarefa):
        try:
            arquivos = ArquivoTarefa.objects.filter(tarefa_id=tarefa)
        except ArquivoTarefa.DoesNotExist:
            return Response({'error': 'ArquivoModel nao encontrado.'}, status=404)
        serializer = ArquivoTarefaSerializer(arquivos, many=True)
        return Response(serializer.data) 
