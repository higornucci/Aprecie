# Generated by Django 3.2.9 on 2022-02-08 15:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Reconhecimentos', '0007_log_ciclo_novo_nome_ciclo'),
    ]

    operations = [
        migrations.AddField(
            model_name='log_ciclo',
            name='antigo_nome_ciclo',
            field=models.CharField(default='', max_length=25),
            preserve_default=False,
        ),
    ]
