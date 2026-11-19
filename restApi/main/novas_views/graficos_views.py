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


class GraficoSerieTemporalView(APIView):
    permission_classes = [IsAuthenticated]
    METRICAS_VALIDAS = (
        'clientes',
        'processos',
        'tarefas',
        'processos_ativos',
        'processos_arquivados',
        'processos_peticionar',
        'processos_protocolar',
        'processos_classificacao',
        'processos_grupo',
        'processos_fase',
    )
    DIAS_VALIDOS = (7, 30, 90, 180, 365)

    def get(self, request, format=None):
        metrica = request.query_params.get('metrica', 'tarefas')
        if metrica not in self.METRICAS_VALIDAS:
            return JsonResponse({'error': 'Metrica invalida.'}, status=400)

        try:
            dias = int(request.query_params.get('dias', 30))
        except (TypeError, ValueError):
            dias = 30
        if dias not in self.DIAS_VALIDOS:
            dias = 30

        advogado = request.query_params.get('advogado')
        try:
            advogado_id = int(advogado) if advogado else None
        except (TypeError, ValueError):
            advogado_id = None

        tarefa_tipo = request.query_params.get('tipo')
        if tarefa_tipo not in ('criadas', 'concluidas'):
            tarefa_tipo = None

        parceiro = request.query_params.get('parceiro')
        if parceiro is not None and parceiro != 'null':
            try:
                parceiro = int(parceiro)
            except (TypeError, ValueError):
                parceiro = None

        contrato_param = request.query_params.get('contrato')
        contrato = None
        if contrato_param is not None:
            contrato = contrato_param.lower() in ('true', '1')

        service = GraficoService()
        json_file = service.obter_serie_temporal(
            metrica, dias, request.query_params.get('valor'), advogado_id, tarefa_tipo, parceiro, contrato
        )
        return JsonResponse(json_file, safe=False)