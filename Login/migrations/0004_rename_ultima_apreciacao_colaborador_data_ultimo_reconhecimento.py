# Generated by Django 3.2.9 on 2022-01-10 14:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Login', '0003_colaborador_ultima_apreciacao'),
    ]

    operations = [
        migrations.RenameField(
            model_name='colaborador',
            old_name='ultima_apreciacao',
            new_name='data_ultimo_reconhecimento',
        ),
    ]
