# Generated migration to remove email and profissao fields from Representante model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='representante',
            name='email',
        ),
        migrations.RemoveField(
            model_name='representante',
            name='profissao',
        ),
    ]
