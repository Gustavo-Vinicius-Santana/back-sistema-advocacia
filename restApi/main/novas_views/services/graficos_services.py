from ...models import Processo,GrupoAcao,FaseProcesso,Cliente,Tarefas,Advogado
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta, date, datetime

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
        parceiros = Cliente.objects.values('parceiro__id', 'parceiro__nome').annotate(quantidade=Count('id')).order_by('parceiro__nome')

        json_file = [
            {
                "parceiroId": parceiro['parceiro__id'],
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
            criadas = Tarefas.objects.filter(advogadoCriadorId=advogado.id,deletada=False).count()
            atribuidas = Tarefas.objects.filter(advogadoResponsavelId=advogado.id,deletada=False).count()
            jsonFile.append({
                "advogadoId": advogado.id,
                "advogado": advogado.nome,
                "quantidade": atribuidas,
                "tarefasCriadas": criadas,
                "tarefasAtribuidas": atribuidas,
            })
        return jsonFile

    # metrica -> (model, campo_data, filtros extras)
    METRICAS_SERIE_TEMPORAL = {
        'clientes': (Cliente, 'dataCadastro', {}),
        'processos': (Processo, 'dataCriacao', {}),
        'tarefas': (Tarefas, 'dataInicio', {'deletada': False}),
        'processos_ativos': (Processo, 'dataCriacao', {'status': 'ativo'}),
        'processos_arquivados': (Processo, 'dataCriacao', {'status': 'arquivado'}),
        'processos_peticionar': (Processo, 'dataCriacao', {'tipoAcao__nome__iexact': 'peticionar'}),
        'processos_protocolar': (Processo, 'dataCriacao', {'tipoAcao__nome__iexact': 'protocolar'}),
        'processos_classificacao': (Processo, 'dataCriacao', {}),
        'processos_grupo': (Processo, 'dataCriacao', {}),
        'processos_fase': (Processo, 'dataCriacao', {}),
    }

    # metrica -> lookup ORM aplicado com o parâmetro `valor`
    CAMPOS_FILTRO_VALOR = {
        'processos_classificacao': 'classificacao',
        'processos_grupo': 'grupoAcao__nome__iexact',
        'processos_fase': 'fase__nome__iexact',
    }

    def obter_serie_temporal(self, metrica: str, dias: int, valor: str = None, advogado_id=None, tarefa_tipo: str = None, parceiro=None, contrato=None) -> list:
        """
        Retorna a quantidade de registros criados por dia nos últimos `dias` dias.
        Para períodos longos (acima de 2 meses), agrupa por mês.
        Formato: [{ "data": "YYYY-MM-DD", "quantidade": int }, ...]
        Para metrica='tarefas', inclui também "concluidas" por dia/mês.
        Com advogado_id e tarefa_tipo='criadas', conta tarefas criadas pelo
        advogado (advogadoCriadorId) por dataInicio; com 'concluidas', conta
        tarefas concluídas para o advogado (advogadoResponsavelId) por dataConclusao.
        """
        if metrica not in self.METRICAS_SERIE_TEMPORAL:
            return []

        model, campo_data, filtros_base = self.METRICAS_SERIE_TEMPORAL[metrica]
        filtros_extra = dict(filtros_base)
        campo_valor = self.CAMPOS_FILTRO_VALOR.get(metrica)
        if campo_valor and valor:
            filtros_extra[campo_valor] = valor
        if advogado_id and metrica == 'tarefas':
            if tarefa_tipo == 'criadas':
                filtros_extra['advogadoCriadorId'] = advogado_id
            elif tarefa_tipo == 'concluidas':
                campo_data = 'dataConclusao'
                filtros_extra['advogadoResponsavelId'] = advogado_id
            else:
                filtros_extra['advogadoResponsavelId'] = advogado_id
        if parceiro is not None and metrica == 'clientes':
            if parceiro == 'null':
                filtros_extra['parceiro__isnull'] = True
            else:
                filtros_extra['parceiro_id'] = parceiro
        if contrato is not None and metrica == 'clientes':
            filtros_extra['contrato'] = contrato
        hoje = timezone.localdate()
        inicio = hoje - timedelta(days=dias - 1)
        mensal = dias > 62

        if mensal:
            # Um ponto por mês, a partir do mês de `inicio` até o mês atual
            periodo = []
            ano, mes = inicio.year, inicio.month
            while date(ano, mes, 1) <= hoje:
                periodo.append(date(ano, mes, 1))
                mes += 1
                if mes == 13:
                    mes = 1
                    ano += 1
            trunc = TruncMonth
        else:
            periodo = [inicio + timedelta(days=i) for i in range(dias)]
            trunc = TruncDate

        filtros = {
            f'{campo_data}__date__gte': inicio,
            **filtros_extra,
        }

        contagens = {
            (k.date() if isinstance(k, datetime) else k): v
            for k, v in model.objects
            .filter(**filtros)
            .annotate(dia=trunc(campo_data))
            .values('dia')
            .annotate(total=Count('id'))
            .values_list('dia', 'total')
        }

        resultado = [
            {
                "data": dia.isoformat(),
                "quantidade": contagens.get(dia, 0),
            }
            for dia in periodo
        ]

        if metrica == 'tarefas' and tarefa_tipo is None:
            filtros_conclusao = {
                'deletada': False,
                'dataConclusao__date__gte': inicio,
            }
            if advogado_id:
                filtros_conclusao['advogadoResponsavelId'] = advogado_id
            contagens_concluidas = {
                (k.date() if isinstance(k, datetime) else k): v
                for k, v in Tarefas.objects
                .filter(**filtros_conclusao)
                .annotate(dia=trunc('dataConclusao'))
                .values('dia')
                .annotate(total=Count('id'))
                .values_list('dia', 'total')
            }
            for item in resultado:
                dia = date.fromisoformat(item['data'])
                item['concluidas'] = contagens_concluidas.get(dia, 0)

        return resultado
    