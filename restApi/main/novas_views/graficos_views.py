from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..models import Advogado,Tarefas,Processo,GrupoAcao,FaseProcesso,Cliente,Parceiros
from django.http import JsonResponse
from django.db.models import Count



class GraficosProcessosTipoView(APIView):
    
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        processosRuins = Processo.objects.filter(classificacao = 'ruim').count()
        processosRegulares = Processo.objects.filter(classificacao = 'regular').count()
        processosBons = Processo.objects.filter(classificacao = 'bom').count()
        processosExcelentes = Processo.objects.filter(classificacao = 'excelente').count()

        jsonFile = [
            {
                "classificacao":"ruim",
                "quantidade":processosRuins,
            },
            {
                "classificacao":"regular",
                "quantidade":processosRegulares,
            },
            {
                "classificacao":"bom",
                "quantidade":processosBons,
            },
            {
                "classificacao":"excelente",
                "quantidade":processosExcelentes,
            }

        ]
        return JsonResponse(jsonFile, safe=False)
    
    
class GraficosProcessosGrupoView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        grupos = (
            GrupoAcao.objects
            .annotate(quantidade=Count('processo'))
            .values('nome', 'quantidade')
        )

        json_file = [
            {
                "grupo": g['nome'],
                "quantidade": g['quantidade']
            }
            for g in grupos
        ]

        return JsonResponse(json_file, safe=False)
    

class GraficosProcessosFaseView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        try:
        # Agrupa e conta processos por fase
            fases = (
                FaseProcesso.objects
                .annotate(quantidade=Count('processo'))  # Conta os processos relacionados
                .values('nome', 'quantidade')
                .order_by('nome')
            )

            # Estrutura do JSON
            json_data = [
                {
                    "fase": fase['nome'],
                    "quantidade": fase['quantidade']
                }
                for fase in fases
            ]

            return JsonResponse(json_data, safe=False)
    
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        

class GraficosProcessosProtocolarPeticionarView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        processosProtocolar = Processo.objects.filter(tipoAcao__nome__iexact='protocolar').count()
        processosPeticionar = Processo.objects.filter(tipoAcao__nome__iexact='peticionar').count()

        jsonFile = [
            {
                "categoria": "tipo_acao",
                "protocolar": processosProtocolar,    
                "peticionar": processosPeticionar,           
            },
        ]
        return JsonResponse(jsonFile, safe=False)
    
    
class GraficoProcessosStatusView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        processosStatusAtivo = Processo.objects.filter(status = 'ativo').count()
        processoStatusArquivados = Processo.objects.filter(status = 'arquivado').count()
        jsonFile = [
            {
            "categoria":"atual",
            "ativos":processosStatusAtivo,    
            "arquivados":processoStatusArquivados,           
            },
        ]
        return JsonResponse(jsonFile, safe=False)
    
    
class GraficosClientesContratosView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        clientesComcontrato = Cliente.objects.filter(contrato = True).count()
        clientesSemContrato = Cliente.objects.filter(contrato = False).count()

        json_file = [
            {
                "categoria": "clientes",
                "comContrato": clientesComcontrato,
                "semContrato": clientesSemContrato
            }
        ]

        return JsonResponse(json_file, safe=False)
    
    
    
class GraficoClientesParceirosView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        parceiros = Parceiros.objects.annotate(quantidade_clientes=Count('clientes'))
    
        json_file = [
            {
                "parceiro": parceiro.nome,
                "quantidade": parceiro.quantidade_clientes
            }
            for parceiro in parceiros  
        ]
        return JsonResponse(json_file, safe=False)

        
class GraficoTarefasStatusView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        tarefasConcluidas = Tarefas.objects.filter(concluida = True).count()
        tarefasEmAberto = Tarefas.objects.filter(concluida = False).count()
        jsonFile = [
            {
            "status":"concluidas",
            "quantidade":tarefasConcluidas,               
            },
            {
            "status":"em aberto",
            "quantidade":tarefasEmAberto,
            }
        ]
        return JsonResponse(jsonFile, safe=False)


class GraficosTarefasAdvogadoView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        advogados = Advogado.objects.all()
        jsonFile = []
        for advogado in advogados:
            count = Tarefas.objects.filter(advogadoResponsavelId=advogado.id,deletada=False).count()
            jsonFile.append({
                "advogado": advogado.nome,
                "quantidade": count
            })
        return JsonResponse(jsonFile, safe=False)