from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager,PermissionsMixin

class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=20, unique=True)
    dataNascimento = models.DateField(blank=True, null=True)
    profissao = models.CharField(max_length=255,blank=True)
    parceiro = models.CharField(max_length=255,blank=True) 
    inss = models.CharField(max_length=255,blank=True)
    cep = models.CharField(max_length=20,blank=True)
    complemento = models.CharField(max_length=255,blank=True)
    contrato = models.BooleanField(default=True)
    contactadoPor = models.CharField(max_length=255,blank=True)
    motivo = models.TextField(blank=True)
    rua = models.CharField(max_length=255,blank=True)
    numero = models.IntegerField(null=True)
    cidade = models.CharField(max_length=255,blank=True)
    estado = models.CharField(max_length=255,blank=True)
    bairro = models.CharField(max_length=255,blank=True)
    observacoes = models.TextField(blank=True)
    foto = models.URLField(max_length=500, blank=True, null=True)
    contactado = models.BooleanField(default=False)
    """o Django não consegue criar campos apos a leitura da classe, então o
    campo motivo deve ser criado e ignorado caso c/ontrato for TRUE,
    garantido que seja escrito se for False pelo validation error la no serializer.py.
    #Atualização: 14/07/2025 Contrato e motivo foram removidos"""
    
    """Bug no retorno das fotos:16/07/2025 
        O django não retorna a foto quando eu acesso via browser.
    """
    
    
   
    def __str__(self):
        return f'Cliente {self.nome}'
    
    
class Representante(models.Model):
    nome = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20,unique=True)
    cpf = models.CharField(max_length=14,unique=True)
    cep = models.CharField(max_length=10)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True, related_name='representantes')
    rua = models.CharField(max_length=255)
    numero = models.IntegerField(default=0)
    cidade = models.CharField(max_length=255)
    estado = models.CharField(max_length=255)
    bairro = models.CharField(max_length=255)
    complemento = models.CharField(max_length=255,blank=True)
    observacoes = models.TextField(blank=True)


class ClienteEspera(models.Model):
    nome = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20, default="Sem telefone.", unique=True)
    observacoes = models.TextField(blank=True)
    IdAdvogado = models.IntegerField(default=0)
    cpf = models.CharField(max_length=14, blank=True,unique=True)
    dataNascimento = models.DateField(blank=True,default='2000-01-01')

#Comentando para teste de commit 


class Parceiros(models.Model):
    nome = models.CharField(max_length=255)
    email = models.EmailField(default='nenhum@provedor.com', unique=True)
    telefone = models.CharField(max_length=20, default="Sem telefone.", unique=True)
    cpf = models.CharField(max_length=18, default="Sem CNPJ.",unique=True)
    rua = models.CharField(max_length=255,blank=True)
    numero = models.IntegerField(default=0)
    cidade = models.CharField(max_length=255,blank=True)
    estado = models.CharField(max_length=255,blank=True)
    bairro = models.CharField(max_length=255,blank=True)
    observacoes = models.TextField(blank=True)
    
    
class Escritorios(models.Model):
    nome = models.CharField(max_length=255)
    rua = models.CharField(max_length=255,blank=True)
    numero = models.IntegerField(default=0)
    estado = models.CharField(max_length=255,blank=True)
    complemento = models.CharField(max_length=255,blank=True)
    cep = models.CharField(max_length=20,blank=True)
    cidade = models.CharField(max_length=255,blank=True)
    bairro = models.CharField(max_length=255,blank=True)


class Advogado(AbstractBaseUser, PermissionsMixin):
    nome = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(default='nenhum@provedor.com', unique=True)
    oab = models.CharField(max_length=20, default='Nenhuma OAB',blank=True,null=True)
    foto = models.URLField(max_length=500, blank=True, null=True)
    #Django pede essas paradas pra o login, o nome é autoexplicativo
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    def __str__(self):
        return self.nome
    
    class AdvogadoManager(BaseUserManager,models.Manager):
        def create_user(self, email, password=None, **extra_fields):
            """
            Cria e retorna um advogado com um email e senha.
            """
            if not email:
                raise ValueError("O email é obrigatório")
            email = self.normalize_email(email)
            advogado = self.model(email=email, **extra_fields)
            advogado.set_password(password)
            advogado.save(using=self._db)
            return advogado

        def create_superuser(self, email, password=None, **extra_fields):
            """
            Cria e retorna um superadvogado com privilégios de admin.
            """
            extra_fields.setdefault('is_staff', True)
            extra_fields.setdefault('is_superuser', True)
            return self.create_user(email, password, **extra_fields)

        def get_by_natural_key(self, email):
            """
            Retorna o advogado usando o email.
            """
            return self.get(email=email)
    
    #relacionando as duas classes
    #A classe manager server pra adicionar mais funções de outra classe herdada
    objects = AdvogadoManager()
    
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome','telefone']   
    
    def __str__(self):
        
        return self.nome
   
    
    def get_by_natural_key(self, email):
        return self.get(email=email)
    
    

    # @classmethod
    # def create_superuser(cls, email, password=None, **extra_fields):
    #     """
    #     Cria e retorna um superadvogado com privilégios de admin.
    #     """
    #     extra_fields.setdefault('is_staff', True)
    #     extra_fields.setdefault('is_superuser', True)
    #     return cls.create_user(email, password, **extra_fields)


class Processo(models.Model):
    titulo = models.CharField(max_length=255,blank=True)
    numeroProcesso = models.CharField(max_length=50, unique=True)
    STATUS_CHOICES = [('ativo','Ativo'),('arquivado','Arquivado')]
    status = models.CharField(max_length=50,choices=STATUS_CHOICES, default='ativo')
    clienteId = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    advogadoCriadorId = models.ForeignKey(Advogado, on_delete=models.CASCADE)
    grupoAcao=  models.ForeignKey('GrupoAcao', on_delete=models.PROTECT)
    tipoAcao = models.ForeignKey('TipoAcao', on_delete=models.PROTECT, blank=True)
    fase = models.ForeignKey('FaseProcesso', on_delete=models.PROTECT)
    etapa = models.ForeignKey('EtapaProcesso', on_delete=models.PROTECT, blank=True)
    dataContrato = models.DateTimeField(default='2000-01-01 00:00:00', blank=True)
    CLASSIFICACAO_CHOICES = [('ruim','Ruim'),('regular','Regular'),('bom','Bom'),('excelente','Excelente')]
    classificacao = models.CharField(max_length=50, blank=True, choices=CLASSIFICACAO_CHOICES, default='regular')
    descricao = models.TextField(blank=True)
    prioritario = models.BooleanField(default=False)
    concluido = models.BooleanField(default=False)
    

class GrupoAcao(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self):
        return self.nome

class TipoAcao(models.Model):
    nome = models.CharField(max_length=100)
    grupoAcao = models.ForeignKey('GrupoAcao', on_delete=models.CASCADE)
    def __str__(self):
        return self.nome
        

class FaseProcesso(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self):
        return self.nome

class EtapaProcesso(models.Model):
    nome = models.CharField(max_length=100)
    faseProcesso = models.ForeignKey('FaseProcesso', on_delete=models.CASCADE)
    def __str__(self):
        return self.nome

class Tarefas(models.Model):
    advogadoCriadorId = models.ForeignKey(Advogado, on_delete=models.CASCADE,related_name='advogadoCriador', blank=True)
    advogadoResponsavelId = models.ForeignKey(Advogado, on_delete=models.CASCADE,related_name='advogadoResponsavel')
    processoOrigemId = models.ForeignKey(Processo, on_delete=models.CASCADE,default=0)    
    tipoTarefa = models.ForeignKey('TipoTarefa', on_delete=models.PROTECT, null=True, blank=True)
    descricao = models.CharField(max_length=255,blank=True) #vai se atualizar timeline
    dataInicio = models.DateTimeField(auto_now_add=True)
    prazoFinal = models.DateTimeField(null=True, blank=True)
    urgente = models.BooleanField(default=False,blank=True)
    #deletadas = models.BooleanField(default=False,blank=True)
    concluida = models.BooleanField(default=False,blank=True)
    deletada = models.BooleanField(default=False)
    deletadaPor = models.CharField(max_length=255, default="Ninguem", blank=True)
    STATUS_CHOICES = [('em aberto','Em aberto'),('atrasada','Atrasada'),('perto do prazo','Perto do prazo')]
    status = models.CharField(choices=STATUS_CHOICES,max_length=50, default='em aberto' ) #choices APAGADA,CONCLUIDA,EM ANDAMENTO
    observacoes = models.TextField(default="Nenhuma observação.", blank=True)



class TipoTarefa(models.Model):
    nome = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nome        
        
class HistoricoTarefas(models.Model):
    tarefaId = models.ForeignKey(Tarefas, on_delete=models.CASCADE)
    dataHora = models.DateTimeField(auto_now_add=True)
    acao = models.CharField(max_length=255,blank=True) #vai se atualizar timeline
    
    def __str__(self):
        return f'Histórico da Tarefa {self.tarefaId.id} - {self.dataHora}'
    
    

class Documentos(models.Model):
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100)
    documento = models.TextField()



class ArquivoModel(models.Model):
    cliente_id = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nome = models.CharField(max_length=255,default='Sem nome')
    arquivo = models.TextField() #Vai armazenar o URL do arquivo que fara a renderização no front
    
    

class ArquivoTarefa(models.Model):
    tarefa_id = models.ForeignKey(Tarefas, on_delete=models.CASCADE)
    nome = models.CharField(max_length=255,default='Sem nome')
    arquivo = models.TextField() #Vai armazenar o URL do arquivo que fara a renderização no front