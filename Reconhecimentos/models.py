﻿import django
from datetime import date
from django.db import models
from Aprecie.base import ExcecaoDeDominio

class Pilar(models.Model):
  nome = models.CharField(max_length=200)
  descricao = models.CharField(max_length=1000)

  def __eq__(self, other):
    return self.nome == other.nome

class DescricaoDoValor(models.Model):
  descricao = models.CharField(max_length=100)

class Valor(models.Model):
  nome = models.CharField(max_length=200)
  resumo = models.CharField(max_length=200)
  descricoes = models.ManyToManyField(DescricaoDoValor)

  @property
  def frases_de_descricao(self):
    return list(self.descricoes.values_list('descricao', flat=True))

class Reconhecimento(models.Model):
  reconhecedor = models.ForeignKey('Login.Colaborador', related_name='reconhecedor', on_delete=models.CASCADE)
  reconhecido = models.ForeignKey('Login.Colaborador', related_name='reconhecido', on_delete=models.CASCADE)
  feedback = models.ForeignKey('Feedback', related_name='feedback', on_delete=models.CASCADE)
  pilar = models.ForeignKey(Pilar, on_delete=models.CASCADE)
  data = models.DateField(auto_now_add=True)

  def alterar_feedback(self, novo_feedback, reconhecedor):
    if self.reconhecedor != reconhecedor:
      raise ExcecaoDeDominio('O reconhecimento só pode ser alterado por quem o elaborou')
      
    if self.data != date.today():
      raise ExcecaoDeDominio('O reconhecimento só pode ser alterado no mesmo dia de sua realização')

    self.feedback = novo_feedback

class ReconhecimentoHistorico(models.Model):
  reconhecedor = models.ForeignKey('Login.Colaborador', related_name='reconhecedor_historico', on_delete=models.CASCADE)
  reconhecido = models.ForeignKey('Login.Colaborador', related_name='reconhecido_historico', on_delete=models.CASCADE)
  feedback = models.ForeignKey('Feedback', related_name='feedback_historico', on_delete=models.CASCADE)
  valor = models.ForeignKey(Valor, on_delete=models.CASCADE)
  data = models.DateField()

class Feedback(models.Model):
  situacao = models.CharField(max_length=1000)
  comportamento = models.CharField(max_length=1000)
  impacto = models.CharField(max_length=1000)

  def __eq__(self, other):
    return self.situacao == other.situacao and self.comportamento == other.comportamento and self.impacto == other.impacto
