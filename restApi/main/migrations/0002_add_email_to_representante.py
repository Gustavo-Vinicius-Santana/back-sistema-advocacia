# Generated migration to add missing fields to Representante model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='representante',
            name='email',
            field=models.EmailField(blank=True, default='nenhum@provedor.com', unique=True),
        ),
        migrations.AddField(
            model_name='representante',
            name='profissao',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='representante',
            name='cep',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='representante',
            name='numero',
            field=models.IntegerField(default=0),
        ),
    ]
