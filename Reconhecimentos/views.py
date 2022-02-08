﻿from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import formats
from django.db.models import Count
from django.core.paginator import Paginator
from datetime import date

from operator import attrgetter
from Login.models import Colaborador
from Reconhecimentos.models import Pilar, Reconhecimento, Feedback, Ciclo, LOG_Ciclo
from Reconhecimentos.services import Notificacoes
from django.core.paginator import Paginator

def reconhecer(requisicao):
  id_do_reconhecedor = requisicao.POST['id_do_reconhecedor']
  id_do_reconhecido = requisicao.POST['id_do_reconhecido']
  id_do_pilar = requisicao.POST['id_do_pilar']
  descritivo = requisicao.POST['descritivo']

  reconhecido = Colaborador.objects.get(id = id_do_reconhecido)
  reconhecedor = Colaborador.objects.get(id = id_do_reconhecedor)
  pilar = Pilar.objects.get(id = id_do_pilar)
  feedback = Feedback.objects.create(descritivo = descritivo)

  reconhecido.reconhecer(reconhecedor, pilar, feedback)
  Notificacoes.notificar_no_chat(reconhecedor, reconhecido, pilar)

  return JsonResponse({})

def ultimos_reconhecimentos(requisicao):
  reconhecimentos = Reconhecimento.objects.all().order_by('-id')

  pagina_atual = int(requisicao.GET['pagina_atual'])
  paginacao = Paginator(reconhecimentos, 10)
  pagina = paginacao.page(pagina_atual)

  reconhecimentos_mapeados = list(map(lambda reconhecimento: {
    'id': reconhecimento.pk,
    'id_do_reconhecedor': reconhecimento.reconhecedor.id,
    'nome_do_reconhecedor': reconhecimento.reconhecedor.nome_abreviado,
    'id_do_reconhecido': reconhecimento.reconhecido.id,
    'nome_do_reconhecido': reconhecimento.reconhecido.nome_abreviado,
    'pilar': reconhecimento.pilar.nome,
    'descritivo': reconhecimento.feedback.descritivo,
    'data': reconhecimento.data
  }, pagina.object_list))

  retorno = {
    'total_de_paginas': paginacao.num_pages,
    'pagina_atual': pagina.number,
    'reconhecimentos': reconhecimentos_mapeados
  }

  return JsonResponse(retorno, safe=False)

def ultima_data_de_publicacao(requisicao, id_do_reconhecedor):
  reconhecedor = Colaborador.objects.get(id = id_do_reconhecedor)

  ultima_data = reconhecedor.obter_ultima_data_de_publicacao()

  resposta = {
    'ultimaData': ultima_data
  }

  return JsonResponse(resposta)

def definir_data_de_publicacao(requisicao, id_do_reconhecedor):
  reconhecedor = Colaborador.objects.get(id = id_do_reconhecedor)

  reconhecedor.definir_ultima_data_de_publicacao(date.today())

  return JsonResponse ({})

def reconhecimentos_do_colaborador(requisicao, id_do_reconhecido):
  reconhecido = Colaborador.objects.get(id = id_do_reconhecido)
  pilares = list(map(lambda pilar: {
    'id': pilar.id,
    'nome': pilar.nome,
    'descricao': pilar.descricao,
    'possui_reconhecimentos': len(reconhecido.reconhecimentos_por_pilar(pilar)) > 0,
    'quantidade_de_reconhecimentos': len(reconhecido.reconhecimentos_por_pilar(pilar))
  }, Pilar.objects.all()))

  return JsonResponse({ 'id': reconhecido.id, 'nome': reconhecido.nome_abreviado, 'pilares': pilares }, safe = False)

def contar_reconhecimentos(requisicao):
   colaboradores = map(lambda colaborador: { 
     'nome': colaborador.nome_abreviado, 
     'apreciacoes': colaborador.contar_todos_reconhecimentos(), 
     'foto': colaborador.foto
     }, Colaborador.objects.all()[:10])
   
   colaboradoresOrdenados= sorted(colaboradores, key=lambda x: x["apreciacoes"], reverse=True)

   return JsonResponse({'colaboradores': list(colaboradoresOrdenados)})


def reconhecimentos_por_reconhecedor(requisicao, id_do_reconhecido):
  reconhecedores = Reconhecimento.objects.filter(reconhecido = id_do_reconhecido) \
    .values('reconhecedor__nome', 'reconhecedor', 'reconhecedor__id', 'pilar__id') \
    .annotate(quantidade_de_reconhecimentos=Count('reconhecedor'))

  for reconhecedor in reconhecedores:
    reconhecedor['reconhecedor__nome'] = Colaborador.obter_primeiro_nome(reconhecedor['reconhecedor__nome'])

  return JsonResponse({ 'reconhecedores': list(reconhecedores) })

def todas_as_apreciacoes(requisicao, id_do_reconhecido):
  reconhecido = Colaborador.objects.get(id=id_do_reconhecido)
  
  apreciacoes = reconhecido.reconhecimentos() \
    .values('data', 'pilar__nome', 'feedback__descritivo', \
            'reconhecedor__nome', 'reconhecedor__id', 'reconhecido__nome') \
    .order_by('-data', '-id')

  resposta = {
    'apreciacoes': list(apreciacoes)
  }

  return JsonResponse(resposta)

def todos_os_pilares_e_colaboradores(requisicao):
    pilares = map(lambda pilar: { 'id': pilar.id, 'nome': pilar.nome }, Pilar.objects.all())
    colaboradores = map(lambda colaborador: { 'id_colaborador': colaborador.id, 'nome': colaborador.nome_abreviado}, Colaborador.objects.all())

    retorno = {
      'pilares': list(pilares),
      'colaboradores': list(colaboradores)
    }

    return JsonResponse(retorno, safe=False)

def reconhecimentos_por_pilar(requisicao, id_do_reconhecido, id_do_pilar):
  reconhecido = Colaborador.objects.get(id=id_do_reconhecido)
  pilar = Pilar.objects.get(id=id_do_pilar)
  reconhecimentos = reconhecido.reconhecimentos_por_pilar(id_do_pilar) \
    .values('data', 'feedback__descritivo', \
            'reconhecedor__nome', 'reconhecedor__id') \
    .order_by('-data', '-id')

  resposta = {
    'id_do_pilar': pilar.id,
    'nome_do_pilar': pilar.nome,
    'descricao_do_pilar': pilar.descricao,
    'id_do_reconhecido': reconhecido.id,
    'nome_do_reconhecido': reconhecido.nome_abreviado,
    'reconhecimentos': list(reconhecimentos)
  }

  return JsonResponse(resposta)

def definir_ciclo(requisicao):
  nome_ciclo = requisicao.POST["nome_ciclo"]
  data_inicial = requisicao.POST["data_inicial"]
  data_final = requisicao.POST["data_final"]
  id_usuario_que_modificou = requisicao.POST["usuario_que_modificou"]
  
  ciclo = Ciclo(nome=nome_ciclo, data_inicial=data_inicial, data_final= data_final)
  ciclo.save()

  usuario_que_modificou = Colaborador.objects.get(id=id_usuario_que_modificou)
  log_Ciclo = LOG_Ciclo(ciclo=ciclo, usuario_que_modificou=usuario_que_modificou,descricao_da_alteracao='Criação do ciclo')
  log_Ciclo.save()

  return JsonResponse({})


def alterar_ciclo(requisicao):
  # Nessa requisicao precisamos pegar as infos antigas e alocar no log
  # Assim o log vai ter estaticamente as infos do ciclo antigo
  # Temos que pegar via requisicao os dados antigos
  # O nome antigo
  # A data antiga
  # Armazenar no log
  id_ciclo = requisicao.POST["id_ciclo"]
  data_inicial = requisicao.POST["data_inicial"]
  data_final = requisicao.POST["data_final"]
  id_usuario_que_modificou = requisicao.POST["usuario_que_modificou"]
  novo_nome_ciclo = requisicao.POST["novo_nome_ciclo"]
  descricao_da_alteracao =requisicao.POST["descricao_da_alteracao"]
  print(novo_nome_ciclo)
  ciclo = Ciclo.objects.get(id = id_ciclo)
  usuario_que_modificou = Colaborador.objects.get(id=id_usuario_que_modificou)

  log_Ciclo = LOG_Ciclo(ciclo = ciclo, usuario_que_modificou = usuario_que_modificou, 
  descricao_da_alteracao = descricao_da_alteracao, data_final_alterada = ciclo.data_final, antigo_nome_ciclo = ciclo.nome, novo_nome_ciclo = novo_nome_ciclo)
  log_Ciclo.save()

  ciclo.alterar_ciclo(data_final,novo_nome_ciclo)
  ciclo.save()
  print(novo_nome_ciclo)
  return JsonResponse({})
  

def obter_informacoes_ciclo_atual(requisicao):
  ciclo = obter_ciclo_atual()
  log = LOG_Ciclo.objects.filter(ciclo=ciclo).order_by('-data_da_modificacao').first()
  colaborador = Colaborador.objects.get(id=log.usuario_que_modificou.id)

  resposta = {
    'id_ciclo': ciclo.id,
    'nome_do_ciclo': ciclo.nome,
    'data_inicial': ciclo.data_inicial,
    'data_inicial_formatada': ciclo.data_inicial.strftime('%d/%m/%Y'),
    'data_final': ciclo.data_final,
    'data_final_formatada': ciclo.data_final.strftime('%d/%m/%Y'),
    'nome_usuario_que_modificou': colaborador.nome_abreviado,
    'descricao_da_alteracao': log.descricao_da_alteracao,
    'data_ultima_alteracao': log.data_da_modificacao.strftime('%d/%m/%Y'),
    'porcentagem_do_progresso': calcular_porcentagem_progresso(ciclo.data_final, ciclo.data_inicial)
  }
  
  return JsonResponse(resposta)

def ciclos_passados(requisicao):
  ciclos_passados = map(lambda ciclo: { 'id_ciclo': ciclo.id, 'nome': ciclo.nome, 'nome_autor': obter_nome_usuario_que_modificou(ciclo), 'data_inicial': ciclo.data_inicial.strftime('%d/%m/%Y'), 'data_final': ciclo.data_final.strftime('%d/%m/%Y') }, obter_ciclos_passados())

  lista_todos_ciclos_passados = list(ciclos_passados)

  paginator = Paginator(lista_todos_ciclos_passados, 2)

  secoes = []

  for i in range(1, paginator.num_pages + 1):
    secao = {
      'id_secao': i,
      'ciclos': []
    }

    secao["ciclos"] = paginator.page(i).object_list
    secoes.append(secao)
    
  resposta = {
    'secoes': secoes
  }	
  
  return JsonResponse(resposta, safe=False)

def historico_alteracoes(requisicao):
  # Precisa carregar o nome antigo do ciclo
  # O erro acontece porque o historico de alterações mapeia o log com informações do ciclo atual
  # Mas na verdade o log deve armazenar as infos antigas do ciclo que foi alterado
  # Ex: nome_antigo : requisicao da um post no nome antigo
  # data_final_antiga: requisicao da um post na data final do ciclo antigo
  historico_alteracoes = map(lambda LOG_Ciclo: { 'antigo_nome_do_ciclo': LOG_Ciclo.antigo_nome_ciclo, 'nome_autor': LOG_Ciclo.usuario_que_modificou.nome_abreviado, 
  'data_anterior': LOG_Ciclo.data_final_alterada.strftime('%d/%m/%Y'), 'nova_data': LOG_Ciclo.ciclo.data_final.strftime('%d/%m/%Y'), 
  'data_alteracao': LOG_Ciclo.data_da_modificacao.strftime('%d/%m/%Y'), 'motivo_alteracao': LOG_Ciclo.descricao_da_alteracao, 'novo_nome_ciclo' : LOG_Ciclo.novo_nome_ciclo
  },obter_historico_de_alteracoes().order_by('-data_da_modificacao'))


  paginator = Paginator(list(historico_alteracoes), 2)

  secoes = []

  for i in range(1, paginator.num_pages + 1):
    secao = {
      'id_secao': i,
      'LOG_ciclos': []
    }

    secao["LOG_ciclos"] = paginator.page(i).object_list
    secoes.append(secao)
      
  resposta = {
    'secoes': secoes
  }	
  
  return JsonResponse(resposta, safe=False)
  
def calcularPeriodoCiclo(dataFinal, dataInicial):
  periodoCiclo = dataFinal - dataInicial
  return periodoCiclo.days
  
def calcularProgessoEmDias(dataFinal, dataHoje):
  periodoDias = dataFinal - dataHoje
  return periodoDias.days
  
def calcular_porcentagem_progresso(dataFinal, dataInicial):
  dataInicial = dataInicial
  dataFinal = dataFinal

  dataHoje = date.today()
  calculoPeriodoCiclo = calcularPeriodoCiclo(dataFinal, dataInicial)
  calculoProgressoEmDias = calcularProgessoEmDias(dataFinal, dataHoje)

  diferencaPeriodoEProgresso = calculoPeriodoCiclo - calculoProgressoEmDias

  porcentagem_progresso = int(((diferencaPeriodoEProgresso / calculoPeriodoCiclo) * 100))
  return str(porcentagem_progresso)

def obter_ciclo_atual():
  return Ciclo.objects.get(data_final__gte=date.today(), data_inicial__lte=date.today())

def obter_ciclos_passados():
  return Ciclo.objects.filter(data_final__lte=date.today())

def obter_nome_usuario_que_modificou(ciclo):
  log = LOG_Ciclo.objects.get(ciclo=ciclo.id)
  colaborador = Colaborador.objects.get(id=log.usuario_que_modificou.id)
  return colaborador.nome_abreviado

def obter_historico_de_alteracoes():
  log = LOG_Ciclo.objects.all()
  return log
