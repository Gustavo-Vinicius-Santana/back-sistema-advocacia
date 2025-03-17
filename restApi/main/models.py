from django.db import models

class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    rg = models.CharField(max_length=20, unique=True)
    cpf = models.CharField(max_length=14, unique=True)
    sexo = models.CharField(max_length=10)

class Advogado(models.Model):
    nome = models.CharField(max_length=255)
    rg = models.CharField(max_length=20, unique=True)
    cpf = models.CharField(max_length=14, unique=True)
    sexo = models.CharField(max_length=10)

class Processo(models.Model):
    numero = models.CharField(max_length=50, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    advogado = models.ForeignKey(Advogado, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    descricao = models.TextField()
    