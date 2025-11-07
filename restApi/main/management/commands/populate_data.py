# main/management/commands/populate_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from main.models import *
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados iniciais'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando população do banco...')
        
        # Criar Advogados
        advogados_data = [
            {
                'nome': 'Dr. Roberto Almeida',
                'telefone': '(11) 9888-7777',
                'email': 'roberto.almeida@escritorio.com',
                'oab': '123456/SP',
                'password': 'senha123',
                'is_staff': True,
                'is_superuser': True
            },
            {
                'nome': 'Dra. Patricia Lima', 
                'telefone': '(11) 9777-6666',
                'email': 'patricia.lima@escritorio.com',
                'oab': '654321/SP',
                'password': 'senha123',
                'is_staff': True,
                'is_superuser': False
            },
        ]
        
        for adv_data in advogados_data:
            password = adv_data.pop('password')
            advogado, created = Advogado.objects.get_or_create(
                email=adv_data['email'],
                defaults=adv_data
            )
            if created:
                advogado.set_password(password)
                advogado.save()
                self.stdout.write(f'Advogado {advogado.nome} criado')
        
        # Criar Grupos de Ação
        grupos_acao = [
            {'nome': 'Trabalhista'},
            {'nome': 'Cível'},
            {'nome': 'Família'},
            {'nome': 'Empresarial'},
            {'nome': 'Criminal'},
        ]
        
        grupos_obj = {}
        for grupo in grupos_acao:
            obj, created = GrupoAcao.objects.get_or_create(**grupo)
            grupos_obj[grupo['nome']] = obj
            if created:
                self.stdout.write(f'GrupoAcao {obj.nome} criado')
        
        # Criar Tipos de Ação
        tipos_acao = [
            {'nome': 'Reclamação Trabalhista', 'grupoAcao': grupos_obj['Trabalhista']},
            {'nome': 'Indenização por Danos Morais', 'grupoAcao': grupos_obj['Cível']},
            {'nome': 'Divórcio Consensual', 'grupoAcao': grupos_obj['Família']},
            {'nome': 'Ação de Cobrança', 'grupoAcao': grupos_obj['Empresarial']},
        ]
        
        tipos_obj = {}
        for tipo in tipos_acao:
            obj, created = TipoAcao.objects.get_or_create(
                nome=tipo['nome'],
                grupoAcao=tipo['grupoAcao']
            )
            tipos_obj[tipo['nome']] = obj
            if created:
                self.stdout.write(f'TipoAcao {obj.nome} criado')
        
        # Criar Fases
        fases = [
            {'nome': 'Pré-processual'},
            {'nome': 'Postulatória'},
            {'nome': 'Instrutória'},
            {'nome': 'Decisória'},
        ]
        
        fases_obj = {}
        for fase in fases:
            obj, created = FaseProcesso.objects.get_or_create(**fase)
            fases_obj[fase['nome']] = obj
            if created:
                self.stdout.write(f'FaseProcesso {obj.nome} criado')
        
        # Criar Etapas
        etapas = [
            {'nome': 'Triagem Inicial', 'faseProcesso': fases_obj['Pré-processual']},
            {'nome': 'Petição Inicial', 'faseProcesso': fases_obj['Postulatória']},
            {'nome': 'Contestação', 'faseProcesso': fases_obj['Instrutória']},
            {'nome': 'Sentença', 'faseProcesso': fases_obj['Decisória']},
        ]
        
        etapas_obj = {}
        for etapa in etapas:
            obj, created = EtapaProcesso.objects.get_or_create(
                nome=etapa['nome'],
                faseProcesso=etapa['faseProcesso']
            )
            etapas_obj[etapa['nome']] = obj
            if created:
                self.stdout.write(f'EtapaProcesso {obj.nome} criado')
        
        # Criar Clientes
        clientes_data = [
            {
                'nome': 'João Silva',
                'cpf': '123.456.789-00',
                'telefone': '(11) 9999-8888',
                'dataNascimento': '1980-05-15',
                'profissao': 'Engenheiro',
                'cep': '01234-000',
                'rua': 'Rua A',
                'numero': 123,
                'cidade': 'São Paulo',
                'estado': 'SP',
                'bairro': 'Centro',
                'contactado': True
            },
            {
                'nome': 'Maria Santos',
                'cpf': '987.654.321-00', 
                'telefone': '(11) 9777-6666',
                'dataNascimento': '1975-08-22',
                'profissao': 'Advogada',
                'cep': '04567-000',
                'rua': 'Av. B',
                'numero': 456,
                'cidade': 'São Paulo',
                'estado': 'SP', 
                'bairro': 'Jardins',
                'contactado': True
            },
        ]
        
        clientes_obj = {}
        for cliente_data in clientes_data:
            obj, created = Cliente.objects.get_or_create(
                cpf=cliente_data['cpf'],
                defaults=cliente_data
            )
            clientes_obj[cliente_data['nome']] = obj
            if created:
                self.stdout.write(f'Cliente {obj.nome} criado')
        
        # Criar Processos
        processos_data = [
            {
                'titulo': 'Indenização por Danos Morais',
                'numeroProcesso': '0001C.2024.1.00.0001',
                'status': 'ativo',
                'clienteId': clientes_obj['João Silva'],
                'advogadoCriadorId': Advogado.objects.get(email='roberto.almeida@escritorio.com'),
                'grupoAcao': grupos_obj['Cível'],
                'tipoAcao': tipos_obj['Indenização por Danos Morais'],
                'fase': fases_obj['Postulatória'],
                'etapa': etapas_obj['Petição Inicial'],
                'classificacao': 'bom',
                'descricao': 'Ação de indenização por danos morais',
                'prioritario': False,
                'concluido': False
            },
            {
                'titulo': 'Reclamação Trabalhista',
                'numeroProcesso': '0002T.2024.1.00.0002', 
                'status': 'ativo',
                'clienteId': clientes_obj['Maria Santos'],
                'advogadoCriadorId': Advogado.objects.get(email='patricia.lima@escritorio.com'),
                'grupoAcao': grupos_obj['Trabalhista'],
                'tipoAcao': tipos_obj['Reclamação Trabalhista'],
                'fase': fases_obj['Instrutória'],
                'etapa': etapas_obj['Contestação'],
                'classificacao': 'regular', 
                'descricao': 'Reclamação trabalhista por horas extras',
                'prioritario': True,
                'concluido': False
            },
        ]
        
        processos_obj = {}
        for processo_data in processos_data:
            obj, created = Processo.objects.get_or_create(
                numeroProcesso=processo_data['numeroProcesso'],
                defaults=processo_data
            )
            processos_obj[processo_data['titulo']] = obj
            if created:
                self.stdout.write(f'Processo {obj.numeroProcesso} criado')

        # CRIAR TIPOS DE TAREFA
        tipos_tarefa_data = [
            {'nome': 'Petição Inicial'},
            {'nome': 'Audiência'},
            {'nome': 'Recurso'},
            {'nome': 'Diligência'},
            {'nome': 'Consulta Processual'},
            {'nome': 'Contestação'},
            {'nome': 'Prova Pericial'},
            {'nome': 'Sentença'},
            {'nome': 'Protocolo'},
            {'nome': 'Análise Documental'},
            {'nome': 'Reunião com Cliente'},
            {'nome': 'Laudo Técnico'},
            {'nome': 'Cálculos'},
            {'nome': 'Impugnação'},
            {'nome': 'Sustentação Oral'},
        ]
        
        tipos_tarefa_obj = {}
        for tipo_data in tipos_tarefa_data:
            obj, created = TipoTarefa.objects.get_or_create(**tipo_data)
            tipos_tarefa_obj[tipo_data['nome']] = obj
            if created:
                self.stdout.write(f'TipoTarefa {obj.nome} criado')

        # CRIAR TAREFAS
        # Obter advogados
        adv_roberto = Advogado.objects.get(email='roberto.almeida@escritorio.com')
        adv_patricia = Advogado.objects.get(email='patricia.lima@escritorio.com')
        
        # Datas para os prazos
        hoje = timezone.now()
        amanha = hoje + timedelta(days=1)
        semana_que_vem = hoje + timedelta(days=7)
        duas_semanas = hoje + timedelta(days=14)
        
        tarefas_data = [
            # Tarefas para o Processo 1 - Indenização
            {
                'advogadoCriadorId': adv_roberto,
                'advogadoResponsavelId': adv_roberto,
                'processoOrigemId': processos_obj['Indenização por Danos Morais'],
                'tipoTarefa': tipos_tarefa_obj['Petição Inicial'],
                'descricao': 'Elaborar petição inicial detalhada com todos os fundamentos jurídicos',
                'dataInicio': hoje - timedelta(days=5),
                'prazoFinal': hoje + timedelta(days=2),
                'urgente': True,
                'concluida': True,
                'deletada': False,
                'deletadaPor': 'Ninguem',
                'status': 'em aberto',
                'observacoes': 'Incluir jurisprudência recente do STJ'
            },
            {
                'advogadoCriadorId': adv_roberto,
                'advogadoResponsavelId': adv_roberto,
                'processoOrigemId': processos_obj['Indenização por Danos Morais'],
                'tipoTarefa': tipos_tarefa_obj['Análise Documental'],
                'descricao': 'Analisar documentos anexados pelo cliente',
                'dataInicio': hoje,
                'prazoFinal': amanha,
                'urgente': False,
                'concluida': False,
                'deletada': False,
                'deletadaPor': 'Ninguem',
                'status': 'em aberto',
                'observacoes': 'Verificar autenticidade dos comprovantes'
            },
            {
                'advogadoCriadorId': adv_roberto,
                'advogadoResponsavelId': adv_roberto,
                'processoOrigemId': processos_obj['Indenização por Danos Morais'],
                'tipoTarefa': tipos_tarefa_obj['Reunião com Cliente'],
                'descricao': 'Reunião para alinhar estratégia processual',
                'dataInicio': hoje,
                'prazoFinal': semana_que_vem,
                'urgente': False,
                'concluida': False,
                'deletada': False,
                'deletadaPor': 'Ninguem',
                'status': 'em aberto',
                'observacoes': 'Preparar apresentação com timeline do processo'
            },
            
            # Tarefas para o Processo 2 - Trabalhista
            {
                'advogadoCriadorId': adv_patricia,
                'advogadoResponsavelId': adv_patricia,
                'processoOrigemId': processos_obj['Reclamação Trabalhista'],
                'tipoTarefa': tipos_tarefa_obj['Cálculos'],
                'descricao': 'Calcular horas extras e verbas rescisórias',
                'dataInicio': hoje - timedelta(days=3),
                'prazoFinal': hoje + timedelta(days=1),
                'urgente': True,
                'concluida': False,
                'deletada': False,
                'deletadaPor': 'Ninguem',
                'status': 'perto do prazo',
                'observacoes': 'Considerar adicional noturno e horas in itinere'
            },
            {
                'advogadoCriadorId': adv_patricia,
                'advogadoResponsavelId': adv_patricia,
                'processoOrigemId': processos_obj['Reclamação Trabalhista'],
                'tipoTarefa': tipos_tarefa_obj['Audiência'],
                'descricao': 'Preparar documentação para audiência conciliação',
                'dataInicio': hoje,
                'prazoFinal': duas_semanas,
                'urgente': False,
                'concluida': False,
                'deletada': False,
                'deletadaPor': 'Ninguem',
                'status': 'em aberto',
                'observacoes': 'Listar testemunhas e preparar quesitos'
            },
            {
                'advogadoCriadorId': adv_patricia,
                'advogadoResponsavelId': adv_roberto,  # Tarefa delegada
                'processoOrigemId': processos_obj['Reclamação Trabalhista'],
                'tipoTarefa': tipos_tarefa_obj['Prova Pericial'],
                'descricao': 'Solicitar perícia contábil',
                'dataInicio': hoje,
                'prazoFinal': semana_que_vem,
                'urgente': False,
                'concluida': False,
                'deletada': False,
                'deletadaPor': 'Ninguem',
                'status': 'em aberto',
                'observacoes': 'Contatar perito credenciado'
            },
            
            # Tarefas gerais/administrativas
            {
                'advogadoCriadorId': adv_roberto,
                'advogadoResponsavelId': adv_patricia,
                'processoOrigemId': processos_obj['Indenização por Danos Morais'],
                'tipoTarefa': tipos_tarefa_obj['Consulta Processual'],
                'descricao': 'Verificar andamento processual no tribunal',
                'dataInicio': hoje,
                'prazoFinal': amanha,
                'urgente': False,
                'concluida': False,
                'deletada': False,
                'deletadaPor': 'Ninguem',
                'status': 'em aberto',
                'observacoes': 'Certificar-se da distribuição'
            },
            {
                'advogadoCriadorId': adv_patricia,
                'advogadoResponsavelId': adv_patricia,
                'processoOrigemId': processos_obj['Reclamação Trabalhista'],
                'tipoTarefa': tipos_tarefa_obj['Protocolo'],
                'descricao': 'Protocolar petição inicial no fórum',
                'dataInicio': hoje + timedelta(days=1),
                'prazoFinal': hoje + timedelta(days=2),
                'urgente': True,
                'concluida': False,
                'deletada': False,
                'deletadaPor': 'Ninguem',
                'status': 'em aberto',
                'observacoes': 'Levar cópias autenticadas'
            }
        ]
        
        for tarefa_data in tarefas_data:
            obj, created = Tarefas.objects.get_or_create(
                advogadoCriadorId=tarefa_data['advogadoCriadorId'],
                advogadoResponsavelId=tarefa_data['advogadoResponsavelId'],
                processoOrigemId=tarefa_data['processoOrigemId'],
                tipoTarefa=tarefa_data['tipoTarefa'],
                descricao=tarefa_data['descricao'],
                defaults=tarefa_data
            )
            if created:
                self.stdout.write(f'Tarefa "{obj.descricao[:30]}..." criada')
        
        self.stdout.write(self.style.SUCCESS('Banco populado com sucesso!'))
        self.stdout.write(f'Total: {TipoTarefa.objects.count()} tipos de tarefa e {Tarefas.objects.count()} tarefas criadas')