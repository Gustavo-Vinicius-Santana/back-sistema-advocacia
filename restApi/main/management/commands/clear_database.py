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
    help = 'Limpa TODOS os dados do banco de dados, mantendo apenas superusuários'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma a exclusão automaticamente (sem perguntar)'
        )

    def handle(self, *args, **options):
        confirm = options['confirm']

        # Contagem antes
        counts_before = self.get_counts()

        self.stdout.write(self.style.WARNING("=" * 60))
        self.stdout.write(self.style.WARNING("⚠️  LIMPEZA COMPLETA DO BANCO DE DADOS ⚠️"))
        self.stdout.write(self.style.WARNING("=" * 60))

        self.stdout.write("\n📊 Situação atual do banco:")
        for model, count in counts_before.items():
            self.stdout.write(f"   {model}: {count}")

        self.stdout.write(self.style.ERROR("\n🗑️  TODOS os dados serão removidos, EXCETO superusuários!\n"))

        # Confirmação manual
        if not confirm:
            resposta = input("❓ Confirmar exclusão COMPLETA? (Digite SIM): ")
            if resposta != "SIM":
                self.stdout.write(self.style.SUCCESS("\nOperação cancelada."))
                return

        try:
            with transaction.atomic():
                self.clear_data()

            # Contagem depois
            counts_after = self.get_counts()

            self.stdout.write(self.style.SUCCESS("\n✅ Limpeza completa concluída com sucesso!\n"))
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
    # Limpeza COMPLETA dos dados (exceto superusuários)
    # ------------------------------------------------------------
    def clear_data(self):
        self.stdout.write("🧹 Iniciando limpeza COMPLETA...\n")

        # 1. Primeiro: Arquivos e históricos (dependem de tarefas)
        self.delete_with_log(ArquivoTarefa, "📎 Arquivos de Tarefas")
        self.delete_with_log(HistoricoTarefas, "📝 Históricos de Tarefas")
        self.delete_with_log(ArquivoModel, "📁 Arquivos de Clientes")
        self.delete_with_log(Documentos, "📄 Documentos")

        # 2. Segundo: Tarefas (dependem de processos)
        self.delete_with_log(Tarefas, "✅ Tarefas")

        # 3. Terceiro: Processos (dependem de clientes, advogados e estruturas)
        self.delete_with_log(Processo, "⚖️ Processos")

        # 4. Quarto: Representantes e clientes em espera (dependem de clientes/advogados)
        self.delete_with_log(Representante, "👥 Representantes")
        self.delete_with_log(ClienteEspera, "⏳ Clientes em Espera")

        # 5. Quinto: Clientes (dependem de parceiros)
        self.delete_with_log(Cliente, "👤 Clientes")

        # 6. Sexto: Parceiros
        self.delete_with_log(Parceiros, "🤝 Parceiros")

        # 7. Sétimo: Estruturas do sistema
        self.delete_with_log(Escritorios, "🏢 Escritórios")
        self.delete_with_log(TipoTarefa, "🎯 Tipos de Tarefa")
        self.delete_with_log(TipoAcao, "📋 Tipos de Ação")
        self.delete_with_log(GrupoAcao, "📂 Grupos de Ação")
        self.delete_with_log(FaseProcesso, "🔄 Fases")
        self.delete_with_log(EtapaProcesso, "📊 Etapas")
        
        # 8. Oitavo: Advogados NÃO superusuários
        nao_super = Advogado.objects.filter(is_superuser=False)
        if nao_super.exists():
            count = nao_super.count()
            nao_super.delete()
            self.stdout.write(f"⚖️ Advogados não-superusuários: {count} removidos")
        else:
            self.stdout.write("⚖️ Advogados não-superusuários: 0 (já vazio)")

        # Mantém apenas superusuários
        superusers_count = Advogado.objects.filter(is_superuser=True).count()
        self.stdout.write(f"👑 Superusuários mantidos: {superusers_count}")

    # ------------------------------------------------------------
    # Função auxiliar para deletar com log
    # ------------------------------------------------------------
    def delete_with_log(self, model, label):
        count = model.objects.count()
        if count > 0:
            model.objects.all().delete()
            self.stdout.write(f"{label}: {count} removidos")
        else:
            self.stdout.write(f"{label}: 0 (já vazio)")