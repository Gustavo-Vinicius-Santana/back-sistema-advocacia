import os

from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.db import connections
from django.db.models.signals import post_migrate


def create_configured_superuser(sender, using, **kwargs):
    """Cria o administrador configurado por ambiente uma única vez."""
    email = os.getenv('DJANGO_SUPERUSER_EMAIL')
    password = os.getenv('DJANGO_SUPERUSER_PASSWORD')
    nome = os.getenv('DJANGO_SUPERUSER_NOME')
    telefone = os.getenv('DJANGO_SUPERUSER_TELEFONE')

    # Sem uma configuração completa, não cria usuário com dados ou senha padrão.
    if not all((email, password, nome, telefone)):
        return

    user_model = get_user_model()
    if user_model._meta.db_table not in connections[using].introspection.table_names():
        return

    if user_model.objects.filter(email__iexact=email).exists():
        return

    user_model.objects.create_superuser(
        email=email,
        password=password,
        nome=nome,
        telefone=telefone,
    )
    print('Superusuário inicial criado.')


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        post_migrate.connect(
            create_configured_superuser,
            sender=self,
            dispatch_uid='main.create_configured_superuser',
        )
