from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager
import time 


class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=20, default="Sem telefone.")
    sexo = models.CharField(max_length=10)
    dataNascimento = models.DateField()
    nacionalidade = models.CharField(max_length=255,default="Nenhuma nacionalidade.")
    profissao = models.CharField(max_length=255, default="Sem profissão.")
    parceiro = models.CharField(max_length=255, default="Sem parceiro.")
    inss = models.CharField(max_length=255,default="Nenhuma senha.")
    contrato = models.BooleanField(default=False)
    motivo = models.CharField(max_length=255, default="Sem motivo.", blank=True)
    cep = models.CharField(max_length=20, unique=True)
    bairro = models.CharField(max_length=255)
    rua = models.CharField(max_length=255)
    estado = models.CharField(max_length=255)
    observacoes = models.TextField(default="Nenhuma observação.")
    """o Django não consegue criar campos apos a leitura da classe, então o
    campo motivo deve ser criado e ignorado caso contrato for TRUE,
    garantido que seja escrito se for False pelo validation error la no serializer.py."""
    
    
   
    def __str__(self):
        return f'Cliente {self.nome}'
    
        

class Advogado(AbstractBaseUser, models.Model):
    nome = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20)
    sexo = models.CharField(max_length=10)
    email = models.EmailField(default='nenhum@provedor.com', unique=True)
    oab = models.CharField(max_length=20, default='Nenhuma OAB')
    
    #Django pede essas paradas pra o login, o nome é autoexplicativo
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
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
    REQUIRED_FIELDS = ['nome','password','telefone','sexo']   
    
    def __str__(self):
        return self.nome
    def save(self, *args, **kwargs):
        if not self.pk:
            self.password = 'user'
        super(Advogado, self).save(*args, **kwargs)
    
    def get_by_natural_key(self, email):
        return self.get(email=email)
    
    

    @classmethod
    def create_superuser(cls, email, password=None, **extra_fields):
        """
        Cria e retorna um superadvogado com privilégios de admin.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return cls.create_user(email, password, **extra_fields)

class Processo(models.Model):
    numeroProcesso = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=50)
    clienteId = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    advogadoResponsavelId = models.ForeignKey(Advogado, on_delete=models.CASCADE)
    grupoAcao=  models.CharField(max_length=50,default="Sem grupo")
    dataContrato = models.DateTimeField(default='2000-01-01 00:00:00', blank=True)
    prazoContrato = models.DateTimeField(null=True, blank=True)
    classificacao = models.CharField(max_length=50, blank=True)
    descricao = models.TextField()
    prioritario = models.BooleanField(default=False)
    #tipo = adm escolhe o tipo
    #grupo = adm escolhe o grupo
    

class Tarefas(models.Model):
    advogadoCriadorId = models.ForeignKey(Advogado, on_delete=models.CASCADE,related_name='advogadoCriador')
    advogadoResponsavelId = models.ForeignKey(Advogado, on_delete=models.CASCADE,related_name='advogadoResponsavel')
    processoOrigemId = models.ForeignKey(Processo, on_delete=models.CASCADE,default=0)    
    tipoTarefa = models.CharField(max_length=50)
    descricao = models.TextField() #vai se atualizar timeline
    dataInicio = models.DateTimeField(auto_now_add=True)
    prazoFinal = models.DateTimeField(null=True, blank=True)
    urgente = models.BooleanField(default=False)
    status = models.CharField(max_length=50) #choices APAGADA,CONCLUIDA,EM ANDAMENTO
    observacoes = models.TextField(default="Nenhuma observação.")
        