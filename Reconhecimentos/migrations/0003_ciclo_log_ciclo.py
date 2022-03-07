# Generated by Django 3.2.9 on 2022-02-22 14:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Reconhecimentos', '0002_inclusao_dos_pilares'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ciclo',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=25)),
                ('data_inicial', models.DateField()),
                ('data_final', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='LOG_Ciclo',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('data_da_modificacao', models.DateField(auto_now=True)),
                ('descricao_da_alteracao', models.CharField(max_length=63)),
                ('antiga_data_final', models.DateField(default=None, null=True)),
                ('antigo_nome_ciclo', models.CharField(max_length=25)),
                ('novo_nome_ciclo', models.CharField(max_length=25)),
                ('nova_data_alterada', models.DateField(default=None, null=True)),
                ('ciclo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ciclo', to='Reconhecimentos.ciclo')),
                ('usuario_que_modificou', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usuario_que_modificou', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
