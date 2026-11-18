from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import random

from main.models import (
    Cliente, Parceiros, Representante, ClienteEspera, Escritorios, Advogado,
    GrupoAcao, TipoAcao, FaseProcesso, EtapaProcesso, Processo,
    Tarefas, TipoTarefa, HistoricoTarefas, ArquivoModel, ArquivoTarefa, Documentos
)


fake = Faker("pt_BR")


def random_datetime(days_back_max=60, days_forward_max=30):
    """Retorna um datetime aleatório entre `days_back_max` dias atrás e `days_forward_max` no futuro."""
    now = timezone.now()
    delta_days = random.randint(-days_back_max, days_forward_max)
    delta_seconds = random.randint(0, 86399)
    return now + timezone.timedelta(days=delta_days, seconds=delta_seconds)


class Command(BaseCommand):
    help = "Popula o banco de dados com dados fictícios para desenvolvimento"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🛠 Iniciando população do banco..."))

        # -----------------------------------------
        # 1. PARCEIROS
        # -----------------------------------------
        parceiros = []
        for _ in range(5):
            parceiro = Parceiros.objects.create(
                nome=fake.company(),
                email=fake.email(),
                telefone=fake.phone_number(),
                cpf=fake.cnpj(),
                rua=fake.street_name(),
                numero=fake.random_int(1, 999),
                cidade=fake.city(),
                estado="SP",
                bairro=fake.bairro(),
                observacoes="Parceiro gerado automaticamente."
            )
            parceiros.append(parceiro)

        self.stdout.write(self.style.SUCCESS("✔ Parceiros criados"))


        # -----------------------------------------
        # 2. ADVOGADOS
        # -----------------------------------------
        advogados = []
        for _ in range(5):
            advogado = Advogado.objects.create_user(
                email=fake.email(),
                password="123456789012",
                nome=fake.name(),
                telefone=fake.phone_number(),
                oab=str(fake.random_int(10000, 99999)),
            )
            advogados.append(advogado)

        self.stdout.write(self.style.SUCCESS("✔ Advogados criados"))


        # -----------------------------------------
        # 3. CLIENTES
        # -----------------------------------------
        clientes = []
        for _ in range(30):
            cliente = Cliente.objects.create(
                nome=fake.name(),
                dataCadastro=random_datetime(days_back_max=365, days_forward_max=0),
                cpf=fake.cpf(),
                telefone=fake.phone_number(),
                dataNascimento=fake.date_of_birth(minimum_age=18, maximum_age=80),
                profissao=fake.job(),
                inss=fake.word(),
                cep=fake.postcode(),
                rua=fake.street_name(),
                numero=fake.random_int(1, 999),
                cidade=fake.city(),
                estado="SP",
                bairro=fake.bairro(),
                complemento=fake.word(),
                observacoes="Cliente de teste.",
                parceiro=random.choice(parceiros),
                contactado=fake.boolean(),
                contrato=fake.boolean(chance_of_getting_true=70)
            )
            clienteMesmoNome = Cliente.objects.create(
                nome="Gustavo",
                dataCadastro=random_datetime(days_back_max=365, days_forward_max=0),
                cpf=fake.cpf(),
                telefone=fake.phone_number(),
                dataNascimento=fake.date_of_birth(minimum_age=18, maximum_age=80),
                profissao=fake.job(),
                inss=fake.word(),
                cep=fake.postcode(),
                rua=fake.street_name(),
                numero=fake.random_int(1, 999),
                cidade=fake.city(),
                estado="SP",
                bairro=fake.bairro(),
                complemento=fake.word(),
                observacoes="Cliente de teste.",
                parceiro=random.choice(parceiros),
                contactado=fake.boolean(),
                contrato=fake.boolean(chance_of_getting_true=70)
            )
            clientes.append(cliente)
            clientes.append(clienteMesmoNome)

        self.stdout.write(self.style.SUCCESS("✔ Clientes criados"))


        # -----------------------------------------
        # 4. REPRESENTANTES
        # -----------------------------------------
        for cliente in clientes:
            if fake.boolean():
                Representante.objects.create(
                    nome=fake.name(),
                    telefone=fake.phone_number(),
                    cpf=fake.cpf(),
                    email=fake.email(),
                    profissao=fake.job(),
                    cep=fake.postcode(),
                    cliente=cliente,
                    rua=fake.street_name(),
                    numero=fake.random_int(1, 999),
                    cidade=fake.city(),
                    estado="SP",
                    bairro=fake.bairro(),
                    complemento="",
                    observacoes="Representante gerado automaticamente."
                )

        self.stdout.write(self.style.SUCCESS("✔ Representantes criados"))


        # -----------------------------------------
        # 5. CLIENTES ESPERA
        # -----------------------------------------
        for _ in range(5):
            ClienteEspera.objects.create(
                nome=fake.name(),
                telefone=fake.phone_number(),
                observacoes="Cliente aguardando atendimento",
                IdAdvogado=random.choice(advogados).id,
                cpf=fake.cpf()
            )

        self.stdout.write(self.style.SUCCESS("✔ ClientesEspera criados"))


        # -----------------------------------------
        # 6. ESCRITÓRIOS
        # -----------------------------------------
        for _ in range(3):
            Escritorios.objects.create(
                nome=fake.company(),
                rua=fake.street_name(),
                numero=fake.random_int(1, 999),
                estado="SP",
                complemento="",
                cep=fake.postcode(),
                cidade=fake.city(),
                bairro=fake.bairro()
            )

        self.stdout.write(self.style.SUCCESS("✔ Escritórios criados"))


        # -----------------------------------------
        # 7. GRUPO, TIPO, FASE, ETAPA
        # -----------------------------------------
        grupos = []
        for nome in ["Previdenciário", "Trabalhista", "Cível", "Consumidor", "Empresarial"]:
            grupos.append(GrupoAcao.objects.create(nome=nome))

        tipos = []
        for grupo in grupos:
            for nome in ["Inicial", "Recurso", "Revisão", "Petição", "Cumprimento", "Peticionar", "Protocolar"]:
                tipos.append(TipoAcao.objects.create(nome=nome, grupoAcao=grupo))

        fases = []
        for nome in ["Distribuição", "Audiência", "Sentença", "Cumprimento"]:
            fases.append(FaseProcesso.objects.create(nome=nome))

        etapas = []
        for fase in fases:
            for nome in ["Início", "Andamento", "Conclusão", "Pendência"]:
                etapas.append(EtapaProcesso.objects.create(nome=nome, faseProcesso=fase))

        self.stdout.write(self.style.SUCCESS("✔ Grupo/Tipos/Fases/Etapas criados"))


        # -----------------------------------------
        # 8. PROCESSOS (CORRIGIDO - AGORA COM OBSERVACOES)
        # -----------------------------------------
        processos = []
        etapas_por_fase = {}
        for etapa in etapas:
            etapas_por_fase.setdefault(etapa.faseProcesso_id, []).append(etapa)

        tipos_peticionar = [t for t in tipos if t.nome.lower() == "peticionar"]
        tipos_protocolar = [t for t in tipos if t.nome.lower() == "protocolar"]

        for cliente in clientes:
            for _ in range(random.randint(1, 3)):
                data_criacao = random_datetime(days_back_max=365, days_forward_max=5)
                fase_escolhida = random.choice(fases)
                arquivado = random.random() < 0.2

                sorteio_tipo = random.random()
                if sorteio_tipo < 0.15:
                    tipo_acao = random.choice(tipos_peticionar)
                elif sorteio_tipo < 0.30:
                    tipo_acao = random.choice(tipos_protocolar)
                else:
                    tipo_acao = random.choice(tipos)

                processo = Processo.objects.create(
                    numeroProcesso=str(fake.random_int(100000, 999999)),
                    clienteId=cliente,
                    advogadoCriadorId=random.choice(advogados),
                    grupoAcao=tipo_acao.grupoAcao,
                    tipoAcao=tipo_acao,
                    fase=fase_escolhida,
                    etapa=random.choice(etapas_por_fase[fase_escolhida.id]),
                    dataContrato=data_criacao,
                    dataCriacao=data_criacao,
                    status="arquivado" if arquivado else "ativo",
                    classificacao=random.choices(
                        ["ruim", "regular", "bom", "excelente"],
                        weights=[15, 40, 30, 15],
                    )[0],
                    concluido=arquivado or random.random() < 0.1,
                    observacoes="Processo criado automaticamente.",
                    prioritario=fake.boolean()
                )
                processos.append(processo)

        self.stdout.write(self.style.SUCCESS("✔ Processos criados"))


        # -----------------------------------------
        # 9. TAREFAS + HISTÓRICO
        # -----------------------------------------
        tipos_tarefa = []
        for nome in ["Ligação", "Protocolo", "Despacho"]:
            tipos_tarefa.append(TipoTarefa.objects.create(nome=nome))

        for processo in processos:
            for _ in range(random.randint(1, 3)):
                concluida = fake.boolean(chance_of_getting_true=60)
                data_inicio = random_datetime(days_back_max=365, days_forward_max=0)
                data_conclusao = None
                if concluida:
                    # Concluída entre 1 e 10 dias após a criação, sem passar de hoje
                    limite = min(data_inicio + timezone.timedelta(days=10), timezone.now())
                    data_conclusao = data_inicio + timezone.timedelta(
                        seconds=random.randint(0, max(0, int((limite - data_inicio).total_seconds())))
                    )

                tarefa = Tarefas.objects.create(
                    advogadoCriadorId=random.choice(advogados),
                    advogadoResponsavelId=random.choice(advogados),
                    processoOrigemId=processo,
                    tipoTarefa=random.choice(tipos_tarefa),
                    prazoFinal=data_inicio + timezone.timedelta(days=fake.random_int(1, 30)),
                    urgente=fake.boolean(),
                    concluida=concluida,
                    dataConclusao=data_conclusao,
                    deletada=False,
                )
                # dataInicio é auto_now_add: ajusta via update para espalhar no tempo
                Tarefas.objects.filter(pk=tarefa.pk).update(dataInicio=data_inicio)

                HistoricoTarefas.objects.create(
                    tarefaId=tarefa,
                    acao="Tarefa criada automaticamente."
                )

        self.stdout.write(self.style.SUCCESS("✔ Tarefas e históricos criados"))


        # -----------------------------------------
        # 10. ARQUIVOS
        # -----------------------------------------
        for cliente in clientes:
            ArquivoModel.objects.create(
                cliente_id=cliente,
                nome="Documento Cliente",
                arquivo="https://exemplo.com/documento.pdf"
            )

        for processo in processos:
            # Verifica se existem tarefas antes de tentar acessar
            tarefas_processo = processo.tarefas_set.all()
            if tarefas_processo.exists():
                ArquivoTarefa.objects.create(
                    tarefa_id=random.choice(tarefas_processo),
                    nome="Arquivo Tarefa",
                    arquivo="https://exemplo.com/arquivo_tarefa.pdf"
                )

        self.stdout.write(self.style.SUCCESS("✔ Arquivos criados"))


        # -----------------------------------------
        # 11. DOCUMENTOS
        # -----------------------------------------
        for _ in range(5):
            Documentos.objects.create(
                nome=fake.word(),
                tipo=random.choice(["cliente", "processo"]),
                documento="Conteúdo de exemplo"
            )

        self.stdout.write(self.style.SUCCESS("\n🎉 Banco de dados populado com sucesso!"))
