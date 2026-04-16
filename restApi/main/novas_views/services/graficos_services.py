from ...models import Processo,GrupoAcao,FaseProcesso,Cliente,Tarefas,Advogado
from django.db.models import Count

class GraficoService:
    """
    _summary_
        _description:
        Faz a consulta no banco 
        Retorna o jsonfile ja tratado desta forma
        _jsonFile = [
            {
                "classificacao":"ruim",
                "quantidade":processosRuins,
            },
            ....
       
            
    """
    def obter_grafico_processos_tipo(self)->list:
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
        return jsonFile
    def obter_grafico_processos_grupo(self):
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

        return json_file
    
    def obter_grafico_processos_fase(self)->list:
        fases = (
            FaseProcesso.objects
            .annotate(quantidade=Count('processo'))
            .values('nome', 'quantidade')
            .order_by('nome')
        )

        json_data = [
            {
                "fase": fase['nome'],
                "quantidade": fase['quantidade']
            }
            for fase in fases
        ]

        return json_data
    
    def obter_grafico_processos_protocolar_peticionar(self)->list:
        processosProtocolar = Processo.objects.filter(tipoAcao__nome__iexact='protocolar').count()
        processosPeticionar = Processo.objects.filter(tipoAcao__nome__iexact='peticionar').count()

        jsonFile = [
            {
                "categoria": "tipo_acao",
                "protocolar": processosProtocolar,    
                "peticionar": processosPeticionar,           
            },
        ]
        return jsonFile
    
    def obter_grafico_processos_status(self):
        processosStatusAtivo = Processo.objects.filter(status = 'ativo').count()
        processoStatusArquivados = Processo.objects.filter(status = 'arquivado').count()
        jsonFile = [
            {
            "categoria":"atual",
            "ativos":processosStatusAtivo,    
            "arquivados":processoStatusArquivados,           
            },
        ]
        return jsonFile
    
    def obter_grafico_clientes_contratos(self)->list:
        clientesComcontrato = Cliente.objects.filter(contrato = True).count()
        clientesSemContrato = Cliente.objects.filter(contrato = False).count()

        json_file = [
            {
                "categoria": "clientes",
                "comContrato": clientesComcontrato,
                "semContrato": clientesSemContrato
            }
        ]

        return json_file
    
    def obter_grafico_clientes_parceiros(self)->list:
        parceiros = Cliente.objects.values('parceiro__nome').annotate(quantidade=Count('id')).order_by('parceiro__nome')

        json_file = [
            {
                "parceiro": parceiro['parceiro__nome'],
                "quantidade": parceiro['quantidade']
            }
            for parceiro in parceiros
        ]

        return json_file
    
    def obter_grafico_tarefas_status(self)->list:
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
        return jsonFile
    
    def obter_grafico_tarefas_advogado(self)->list:
        advogados = Advogado.objects.all()
        jsonFile = []
        for advogado in advogados:
            count = Tarefas.objects.filter(advogadoResponsavelId=advogado.id,deletada=False).count()
            jsonFile.append({
                "advogado": advogado.nome,
                "quantidade": count
            })
        return jsonFile
    