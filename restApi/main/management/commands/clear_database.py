# main/management/commands/clear_database.py
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import *

class Command(BaseCommand):
    help = 'Limpa todos os dados do banco de dados (exceto superusuários)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Remove TODOS os dados incluindo advogados/superusuários',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma a exclusão sem prompt interativo',
        )

    def handle(self, *args, **options):
        remove_all = options['all']
        confirm = options['confirm']
        
        # Contar registros antes
        counts_before = self.get_counts()
        
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('⚠️  LIMPEZA DO BANCO DE DADOS ⚠️'))
        self.stdout.write(self.style.WARNING('=' * 60))
        
        self.stdout.write(f"\n📊 Dados atuais no banco:")
        for model, count in counts_before.items():
            self.stdout.write(f"   {model}: {count} registros")
        
        if remove_all:
            self.stdout.write(self.style.ERROR(f"\n🗑️  MODO COMPLETO: TODOS os dados serão removidos!"))
        else:
            self.stdout.write(self.style.WARNING(f"\n🗑️  MODO NORMAL: Dados de aplicação serão removidos (superusuários mantidos)"))
        
        if not confirm:
            confirmacao = input("\n❓ Confirmar exclusão? (digite 'SIM' para confirmar): ")
            if confirmacao != 'SIM':
                self.stdout.write(self.style.SUCCESS("✅ Operação cancelada."))
                return
        
        try:
            with transaction.atomic():
                self.clear_data(remove_all)
                
                # Contar registros depois
                counts_after = self.get_counts()
                
                self.stdout.write(self.style.SUCCESS("\n✅ Limpeza concluída com sucesso!"))
                
                self.stdout.write(f"\n📊 Dados restantes no banco:")
                for model, count in counts_after.items():
                    self.stdout.write(f"   {model}: {count} registros")
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro durante a limpeza: {e}"))

    def get_counts(self):
        """Retorna contagem atual de registros"""
        models_to_count = [
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
        for name, model in models_to_count:
            try:
                counts[name] = model.objects.count()
            except:
                counts[name] = 0
                
        return counts

    def clear_data(self, remove_all=False):
        """Executa a limpeza dos dados"""
        
        # Ordem de deleção (respeitando constraints)
        self.stdout.write("\n🧹 Iniciando limpeza...")
        
        # 1. Históricos e relacionamentos
        if HistoricoTarefas.objects.exists():
            count = HistoricoTarefas.objects.count()
            HistoricoTarefas.objects.all().delete()
            self.stdout.write(f"   📝 Históricos de Tarefas: {count} removidos")
        
        if ArquivoTarefa.objects.exists():
            count = ArquivoTarefa.objects.count()
            ArquivoTarefa.objects.all().delete()
            self.stdout.write(f"   📎 Arquivos de Tarefas: {count} removidos")
            
        if ArquivoModel.objects.exists():
            count = ArquivoModel.objects.count()
            ArquivoModel.objects.all().delete()
            self.stdout.write(f"   📁 Arquivos: {count} removidos")
            
        if Documentos.objects.exists():
            count = Documentos.objects.count()
            Documentos.objects.all().delete()
            self.stdout.write(f"   📄 Documentos: {count} removidos")
        
        # 2. Tarefas
        if Tarefas.objects.exists():
            count = Tarefas.objects.count()
            Tarefas.objects.all().delete()
            self.stdout.write(f"   ✅ Tarefas: {count} removidas")
        
        # 3. Processos
        if Processo.objects.exists():
            count = Processo.objects.count()
            Processo.objects.all().delete()
            self.stdout.write(f"   ⚖️ Processos: {count} removidos")
        
        # 4. Representantes e relacionamentos
        if Representante.objects.exists():
            count = Representante.objects.count()
            Representante.objects.all().delete()
            self.stdout.write(f"   👥 Representantes: {count} removidos")
            
        if Parceiros.objects.exists():
            count = Parceiros.objects.count()
            Parceiros.objects.all().delete()
            self.stdout.write(f"   🤝 Parceiros: {count} removidos")
            
        if ClienteEspera.objects.exists():
            count = ClienteEspera.objects.count()
            ClienteEspera.objects.all().delete()
            self.stdout.write(f"   ⏳ Clientes em Espera: {count} removidos")
        
        # 5. Clientes
        if Cliente.objects.exists():
            count = Cliente.objects.count()
            Cliente.objects.all().delete()
            self.stdout.write(f"   👤 Clientes: {count} removidos")
        
        # 6. Estruturas (opcional - manter para não quebrar a aplicação)
        if remove_all:
            # Modo completo - remove TUDO
            if Escritorios.objects.exists():
                count = Escritorios.objects.count()
                Escritorios.objects.all().delete()
                self.stdout.write(f"   🏢 Escritórios: {count} removidos")
                
            if TipoAcao.objects.exists():
                count = TipoAcao.objects.count()
                TipoAcao.objects.all().delete()
                self.stdout.write(f"   📋 Tipos de Ação: {count} removidos")
                
            if GrupoAcao.objects.exists():
                count = GrupoAcao.objects.count()
                GrupoAcao.objects.all().delete()
                self.stdout.write(f"   📂 Grupos de Ação: {count} removidos")
                
            if FaseProcesso.objects.exists():
                count = FaseProcesso.objects.count()
                FaseProcesso.objects.all().delete()
                self.stdout.write(f"   🔄 Fases: {count} removidas")
                
            if EtapaProcesso.objects.exists():
                count = EtapaProcesso.objects.count()
                EtapaProcesso.objects.all().delete()
                self.stdout.write(f"   📊 Etapas: {count} removidas")
                
            if TipoTarefa.objects.exists():
                count = TipoTarefa.objects.count()
                TipoTarefa.objects.all().delete()
                self.stdout.write(f"   🎯 Tipos de Tarefa: {count} removidos")
            
            # Advogados (CUIDADO!)
            if Advogado.objects.exists():
                count = Advogado.objects.count()
                Advogado.objects.all().delete()
                self.stdout.write(f"   ⚖️ Advogados: {count} removidos")
                
        else:
            # Modo normal - mantém estruturas e superusuários
            if Advogado.objects.filter(is_superuser=False).exists():
                count = Advogado.objects.filter(is_superuser=False).count()
                Advogado.objects.filter(is_superuser=False).delete()
                self.stdout.write(f"   ⚖️ Advogados não-superusuários: {count} removidos")
            
            self.stdout.write("   🔧 Estruturas (tipos, fases, grupos) mantidas")
            self.stdout.write("   👑 Superusuários mantidos")