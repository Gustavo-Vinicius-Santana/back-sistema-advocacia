# Generated migration to add email field to Representante model

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
    ]
