from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_campos_criacao_cliente_processo'),
    ]

    operations = [
        migrations.AddField(
            model_name='tarefas',
            name='dataConclusao',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
