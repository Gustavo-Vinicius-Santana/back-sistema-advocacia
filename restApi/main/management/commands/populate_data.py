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


class Command(BaseCommand):
    help = "Popula o banco de dados com dados fictícios para desenvolvimento"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🛠 Iniciando população do banco..."))

        # -----------------------------------------
        # 1. PARCEIROS
        # -----------------------------------------
        parceiros = []
        for _ in range(3):
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
        for _ in range(4):
            advogado = Advogado.objects.create_user(
                email=fake.email(),
                password="123456",
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
        for _ in range(10):
            cliente = Cliente.objects.create(
                nome=fake.name(),
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
                contrato=True
            )
            clienteMesmoNome = Cliente.objects.create(
                nome="Gustavo",
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
                contrato=True
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
        for nome in ["Previdenciário", "Trabalhista", "Cível"]:
            grupos.append(GrupoAcao.objects.create(nome=nome))

        tipos = []
        for grupo in grupos:
            for nome in ["Inicial", "Recurso", "Revisão"]:
                tipos.append(TipoAcao.objects.create(nome=nome, grupoAcao=grupo))

        fases = []
        for nome in ["Distribuição", "Audiência", "Sentença"]:
            fases.append(FaseProcesso.objects.create(nome=nome))

        etapas = []
        for fase in fases:
            for nome in ["Início", "Andamento", "Conclusão"]:
                etapas.append(EtapaProcesso.objects.create(nome=nome, faseProcesso=fase))

        self.stdout.write(self.style.SUCCESS("✔ Grupo/Tipos/Fases/Etapas criados"))


        # -----------------------------------------
        # 8. PROCESSOS
        # -----------------------------------------
        processos = []
        for cliente in clientes:
            processo = Processo.objects.create(
                titulo=f"Processo de {cliente.nome}",
                numeroProcesso=str(fake.random_int(100000, 999999)),
                clienteId=cliente,
                advogadoCriadorId=random.choice(advogados),
                grupoAcao=random.choice(grupos),
                tipoAcao=random.choice(tipos),
                fase=random.choice(fases),
                etapa=random.choice(etapas),
                dataContrato=timezone.now(),
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
            for _ in range(2):
                tarefa = Tarefas.objects.create(
                    advogadoCriadorId=random.choice(advogados),
                    advogadoResponsavelId=random.choice(advogados),
                    processoOrigemId=processo,
                    tipoTarefa=random.choice(tipos_tarefa),
                    prazoFinal=timezone.now() + timezone.timedelta(days=fake.random_int(1, 30)),
                    urgente=fake.boolean(),
                    concluida=fake.boolean(),
                    deletada=False,
                )

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
            ArquivoTarefa.objects.create(
                tarefa_id=random.choice(processo.tarefas_set.all()),
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
                tipo="PDF",
                documento="Conteúdo de exemplo"
            )

        self.stdout.write(self.style.SUCCESS("\n🎉 Banco de dados populado com sucesso!"))
