from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='representante',
            name='profissao',
            field=models.CharField(
                blank=True,
                max_length=255,
            ),
        ),
    ]