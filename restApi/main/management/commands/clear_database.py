# main/management/commands/clear_database.py
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import (
    Cliente, Processo, Tarefas, Advogado, TipoTarefa,
    HistoricoTarefas, Documentos, ArquivoModel, ArquivoTarefa,
    Representante, Parceiros, ClienteEspera, Escritorios,
    GrupoAcao, TipoAcao, FaseProcesso, EtapaProcesso
)

class Command(BaseCommand):
    help = 'Limpa todos os dados do banco de dados (mantém superusuários, exceto com --all)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Remove TODOS os dados incluindo advogados e superusuários'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma a exclusão automaticamente (sem perguntar)'
        )

    def handle(self, *args, **options):
        remove_all = options['all']
        confirm = options['confirm']

        # Contagem antes
        counts_before = self.get_counts()

        self.stdout.write(self.style.WARNING("=" * 60))
        self.stdout.write(self.style.WARNING("⚠️  LIMPEZA DE BANCO DE DADOS ⚠️"))
        self.stdout.write(self.style.WARNING("=" * 60))

        self.stdout.write("\n📊 Situação atual do banco:")
        for model, count in counts_before.items():
            self.stdout.write(f"   {model}: {count}")

        if remove_all:
            self.stdout.write(self.style.ERROR("\n🗑️  MODO COMPLETO: TODOS os dados serão removidos!\n"))
        else:
            self.stdout.write(self.style.WARNING("\n🗑️  MODO NORMAL: Estruturas e superusuários serão mantidos\n"))

        # Confirmação manual
        if not confirm:
            resposta = input("❓ Confirmar exclusão? (Digite SIM): ")
            if resposta != "SIM":
                self.stdout.write(self.style.SUCCESS("\nOperação cancelada."))
                return

        try:
            with transaction.atomic():
                self.clear_data(remove_all)

            # Contagem depois
            counts_after = self.get_counts()

            self.stdout.write(self.style.SUCCESS("\n✅ Limpeza concluída com sucesso!\n"))
            self.stdout.write("📊 Situação após limpeza:")
            for model, count in counts_after.items():
                self.stdout.write(f"   {model}: {count}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Erro durante a limpeza: {e}"))

    # ------------------------------------------------------------
    # Contagem dos registros
    # ------------------------------------------------------------
    def get_counts(self):
        modelos = [
            ('Clientes', Cliente),
            ('Processos', Processo),
            ('Tarefas', Tarefas),
            ('Advogados', Advogado),
            ('TiposTarefa', TipoTarefa),
            ('Históricos', HistoricoTarefas),
            ('Documentos', Documentos),
            ('Arquivos', ArquivoModel),
            ('ArquivosTarefa', ArquivoTarefa),
            ('Representantes', Representante),
            ('Parceiros', Parceiros),
            ('ClientesEspera', ClienteEspera),
            ('Escritórios', Escritorios),
            ('GruposAção', GrupoAcao),
            ('TiposAção', TipoAcao),
            ('Fases', FaseProcesso),
            ('Etapas', EtapaProcesso),
        ]

        counts = {}
        for nome, model in modelos:
            try:
                counts[nome] = model.objects.count()
            except Exception:
                counts[nome] = 0

        return counts

    # ------------------------------------------------------------
    # Limpeza dos dados
    # ------------------------------------------------------------
    def clear_data(self, remove_all=False):
        self.stdout.write("🧹 Iniciando limpeza...\n")

        # 1. Históricos e arquivos
        self.delete_with_log(HistoricoTarefas, "📝 Históricos de Tarefas")
        self.delete_with_log(ArquivoTarefa, "📎 Arquivos de Tarefas")
        self.delete_with_log(ArquivoModel, "📁 Arquivos")
        self.delete_with_log(Documentos, "📄 Documentos")

        # 2. Tarefas
        self.delete_with_log(Tarefas, "✅ Tarefas")

        # 3. Processos
        self.delete_with_log(Processo, "⚖️ Processos")

        # 4. Relacionamentos e vínculos
        self.delete_with_log(Representante, "👥 Representantes")
        self.delete_with_log(Parceiros, "🤝 Parceiros")
        self.delete_with_log(ClienteEspera, "⏳ Clientes em Espera")

        # 5. Clientes
        self.delete_with_log(Cliente, "👤 Clientes")

        # 6. Estruturas
        if remove_all:
            self.delete_with_log(Escritorios, "🏢 Escritórios")
            self.delete_with_log(TipoAcao, "📋 Tipos de Ação")
            self.delete_with_log(GrupoAcao, "📂 Grupos de Ação")
            self.delete_with_log(FaseProcesso, "🔄 Fases")
            self.delete_with_log(EtapaProcesso, "📊 Etapas")
            self.delete_with_log(TipoTarefa, "🎯 Tipos de Tarefa")
            self.delete_with_log(Advogado, "⚖️ Advogados (incluindo superusuários)")
        else:
            # Remove apenas advogados comuns
            nao_super = Advogado.objects.filter(is_superuser=False)
            if nao_super.exists():
                count = nao_super.count()
                nao_super.delete()
                self.stdout.write(f"⚖️ Advogados não-superusuários: {count} removidos")

            self.stdout.write("🔧 Estruturas mantidas.")
            self.stdout.write("👑 Superusuários mantidos.")

    # ------------------------------------------------------------
    # Função auxiliar para deletar com log
    # ------------------------------------------------------------
    def delete_with_log(self, model, label):
        count = model.objects.count()
        if count > 0:
            model.objects.all().delete()
            self.stdout.write(f"{label}: {count} removidos")
