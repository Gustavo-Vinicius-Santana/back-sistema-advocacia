import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_processocliente_and_processo_clientes'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='dataCadastro',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='processo',
            name='dataCriacao',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
