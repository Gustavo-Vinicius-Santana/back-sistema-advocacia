from django.db import models
from django.contrib.auth.models import AbstractBaseUser

class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    rg = models.CharField(max_length=20, unique=True)
    cpf = models.CharField(max_length=14, unique=True)
    sexo = models.CharField(max_length=10)
    telefone = models.CharField(max_length=20)
    fidelizado = models.BooleanField(default=False)
    observacoes = models.TextField(default="Nenhuma observação.")
    endereco = models.CharField(max_length=255)
    nacionalidade = models.CharField(max_length=255)
    profissao = models.CharField(max_length=255)
    #parceiro = adm vai criar uma lista
    senhaInss = models.CharField(max_length=255)
    

class Advogado(AbstractBaseUser, models.Model):
    nome = models.CharField(max_length=255)
    rg = models.CharField(max_length=20, unique=True)
    cpf = models.CharField(max_length=14, unique=True)
    sexo = models.CharField(max_length=10)
    email = models.EmailField(default='nenhum@provedor.com', unique=True)
    oab = models.CharField(max_length=20, unique=True)
    
    #Django pede essas paradas pra o login, o nome é autoexplicativo
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    class AdvogadoManager(models.Manager):
        def create_user(self, email, senha=None, **extra_fields):
            """
            Cria e retorna um advogado com um email e senha.
            """
            if not email:
                raise ValueError("O email é obrigatório")
            email = self.normalize_email(email)
            advogado = self.model(email=email, **extra_fields)
            advogado.set_password(senha)
            advogado.save(using=self._db)
            return advogado

        def create_superuser(self, email, senha=None, **extra_fields):
            """
            Cria e retorna um superadvogado com privilégios de admin.
            """
            extra_fields.setdefault('is_staff', True)
            extra_fields.setdefault('is_superuser', True)
            return self.create_user(email, senha, **extra_fields)

        def get_by_natural_key(self, email):
            """
            Retorna o advogado usando o email.
            """
            return self.get(email=email)
    
    #relacionando as duas classes
    #A classe manager server pra adicionar mais funções de outra classe herdada
    objects = AdvogadoManager()
    
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome','senha','rg','cpf','sexo']   
    
    def __str__(self):
        return self.nome
    def save(self, *args, **kwargs):
        if not self.pk:
            self.senha = 'user'
        super(Advogado, self).save(*args, **kwargs)
    
    def get_by_natural_key(self, email):
        return self.get(email=email)
    
    

    @classmethod
    def create_superuser(cls, email, senha=None, **extra_fields):
        """
        Cria e retorna um superadvogado com privilégios de admin.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return cls.create_user(email, senha, **extra_fields)

class Processo(models.Model):
    numero = models.CharField(max_length=50, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    advogado = models.ForeignKey(Advogado, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    descricao = models.TextField()
    dataCriacao = models.DateTimeField(auto_now_add=True)
    dataEncerramento = models.DateTimeField(null=True, blank=True)
    classificacao = models.CharField(max_length=50)
    prioritario = models.BooleanField(default=False)
    #tipo = adm escolhe o tipo
    #grupo = adm escolhe o grupo
    

class Tarefas(models.Model):
    advogadoResponsavel = models.ForeignKey(Advogado, on_delete=models.CASCADE)
    advogadoCriador = models.ForeignKey(Advogado, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=50)
    descricao = models.TextField() #vai se atualizar timeline
    dataCriacao = models.DateTimeField(auto_now_add=True)
    dataEncerramento = models.DateTimeField(null=True, blank=True)
    prazo = models.IntegerField() #em dias
    status = models.CharField(max_length=50) #choices APAGADA,CONCLUIDA,EM ANDAMENTO
    prioritario = models.BooleanField(default=False)
    #tipo = adm escolhe o tipo
    