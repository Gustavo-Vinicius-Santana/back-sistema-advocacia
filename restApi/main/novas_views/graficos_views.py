from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from .services import GraficoService

#Novas views chamando os Services para obter os dados e retornar o JsonResponse para os gráficos do frontend.

class GraficosProcessosTipoView(APIView):
    
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        service = GraficoService()
        jsonFile = service.obter_grafico_processos_tipo()
        return JsonResponse(jsonFile, safe=False)
    
    
class GraficosProcessosGrupoView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        service = GraficoService()
        json_file = service.obter_grafico_processos_grupo()
        return JsonResponse(json_file, safe=False)
    

class GraficosProcessosFaseView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        try:
            service = GraficoService()
            json_file = service.obter_grafico_processos_fase()
            return JsonResponse(json_file, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        

class GraficosProcessosProtocolarPeticionarView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        service = GraficoService()
        json_file = service.obter_grafico_processos_protocolar_peticionar()
        return JsonResponse(json_file, safe=False)
    
    
class GraficoProcessosStatusView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        service = GraficoService()
        jsonFile = service.obter_grafico_processos_status()
        return JsonResponse(jsonFile, safe=False)
    
    
class GraficosClientesContratosView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        service = GraficoService()
        json_file = service.obter_grafico_clientes_contratos()

        return JsonResponse(json_file, safe=False)
    
    
    
class GraficoClientesParceirosView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        service = GraficoService()
        json_file = service.obter_grafico_clientes_parceiros()
        return JsonResponse(json_file, safe=False)

        
class GraficoTarefasStatusView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        service = GraficoService()
        jsonFile = service.obter_grafico_tarefas_status()
        return JsonResponse(jsonFile, safe=False)


class GraficosTarefasAdvogadoView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        service = GraficoService()
        jsonFile = service.obter_grafico_tarefas_advogado()
        return JsonResponse(jsonFile, safe=False)