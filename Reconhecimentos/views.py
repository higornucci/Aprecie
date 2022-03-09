﻿from django.http import JsonResponse
from django.db.models import Count
from Login.models import Colaborador
from Reconhecimentos.models import Pilar, Reconhecimento, Feedback, Ciclo, LOG_Ciclo
from Reconhecimentos.services import Notificacoes
from django.core.paginator import Paginator
from rolepermissions.decorators import has_role_decorator

from datetime import date, timedelta, datetime

def reconhecer(requisicao):
  id_do_reconhecedor = requisicao.POST['id_do_reconhecedor']
  id_do_reconhecido = requisicao.POST['id_do_reconhecido']
  id_do_pilar = requisicao.POST['id_do_pilar']
  descritivo = requisicao.POST['descritivo']

  reconhecedor = Colaborador.objects.get(id = id_do_reconhecedor)
  
  if verificar_ultima_data_de_publicacao(reconhecedor):
    reconhecido = Colaborador.objects.get(id = id_do_reconhecido)
    pilar = Pilar.objects.get(id = id_do_pilar)
    feedback = Feedback.objects.create(descritivo = descritivo)
    reconhecido.reconhecer(reconhecedor, pilar, feedback)
    Notificacoes.notificar_no_chat(reconhecedor, reconhecido, pilar)
    definir_data_de_publicacao(reconhecedor)

    return JsonResponse({})

  else:
    return JsonResponse(status=403, data = {'mensagem': 'Você já fez um reconhecimento hoje, poderá fazer amanhã novamente!'})

def verificar_ultima_data_de_publicacao(reconhecedor):
  ultima_data = reconhecedor.obter_ultima_data_de_publicacao()

  return not(ultima_data == date.today())
  

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
  

   
def converte_boolean(bool):
    if bool.lower() == 'false':
        return False
    elif bool.lower() == 'true':
        return True
    else:
        raise ValueError("...")

def definir_data_de_publicacao(reconhecedor):
  reconhecedor.definir_ultima_data_de_publicacao(date.today())
  reconhecedor.save()

def reconhecimentos_do_colaborador(requisicao, id_do_reconhecido):
  reconhecido = Colaborador.objects.get(id = id_do_reconhecido)
  pilares = list(map(lambda pilar: {
    'id': pilar.id,
    'nome': pilar.nome,
    'descricao': pilar.descricao,
    'possui_reconhecimentos': len(reconhecido.reconhecimentos_por_pilar(pilar)) > 0,
    'quantidade_de_reconhecimentos': len(reconhecido.reconhecimentos_por_pilar(pilar))
  }, Pilar.objects.all()))

  resposta = {
    'id': reconhecido.id,
    'nome': reconhecido.nome_abreviado,
    'administrador': reconhecido.administrador,
    'pilares': pilares
  }

  return JsonResponse(resposta, safe = False)

def contar_reconhecimentos(requisicao):
   colaboradores = map(lambda colaborador: { 
     'nome': colaborador.nome_abreviado, 
     'apreciacoes': colaborador.contar_todos_reconhecimentos(), 
     'foto': colaborador.foto
     }, sorted(Colaborador.objects.all(), key=lambda x: x.contar_todos_reconhecimentos(), reverse=True)[:10])

   return JsonResponse({'colaboradores': list(colaboradores)})

def reconhecimentos_por_reconhecedor(requisicao, id_do_reconhecido):
  reconhecedores = Reconhecimento.objects.filter(reconhecido = id_do_reconhecido) \
    .values('reconhecedor__nome', 'reconhecedor', 'reconhecedor__id', 'pilar__id') \
    .annotate(quantidade_de_reconhecimentos=Count('reconhecedor'))

  for reconhecedor in reconhecedores:
    reconhecedor['reconhecedor__nome'] = Colaborador.obter_primeiro_nome(reconhecedor['reconhecedor__nome'])

  return JsonResponse({ 'reconhecedores': list(reconhecedores) })

def todas_as_apreciacoes(requisicao, id_do_reconhecido):
  reconhecido = Colaborador.objects.get(id=id_do_reconhecido)

  apreciacoes_recebidas = map(lambda apreciacao: {
    'id': apreciacao.id,
    'data': apreciacao.data,
    'pilar__nome': apreciacao.pilar.nome,
    'feedback__descritivo': apreciacao.feedback.descritivo, 
    'reconhecedor__nome': apreciacao.reconhecedor.nome_abreviado,
    'reconhecedor__id': apreciacao.reconhecedor.id,
    'reconhecido__nome': apreciacao.reconhecido.nome_abreviado
  }, reconhecido.reconhecimentos().order_by('-id'))

  apreciacoes_feitas = map(lambda apreciacao: {
    'id': apreciacao.id,
    'data': apreciacao.data,
    'pilar__nome': apreciacao.pilar.nome,
    'feedback__descritivo': apreciacao.feedback.descritivo, 
    'reconhecedor__nome': apreciacao.reconhecedor.nome_abreviado,
    'reconhecedor__id': apreciacao.reconhecedor.id,
    'reconhecido__nome': apreciacao.reconhecido.nome_abreviado
  }, Reconhecimento.objects.filter(reconhecedor = requisicao.user.id).order_by('-id'))

  apreciacoes = {
    'feitas': list(apreciacoes_feitas),
    'recebidas': list(apreciacoes_recebidas)
  }

  return JsonResponse(apreciacoes)

def todos_os_pilares_e_colaboradores(requisicao):
    pilares = map(lambda pilar: { 
      'id': pilar.id, 
      'nome': pilar.nome 
      }, Pilar.objects.all())

    colaboradores = map(lambda colaborador: { 
      'id_colaborador': colaborador.id, 
      'nome': colaborador.nome_abreviado
      }, Colaborador.objects.all())

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

@has_role_decorator('administrador')
def definir_ciclo(requisicao):
  nome_ciclo = requisicao.POST["nome_ciclo"]
  data_inicial = requisicao.POST["data_inicial"]
  data_final = requisicao.POST["data_final"]
  id_usuario_que_modificou = requisicao.POST["usuario_que_modificou"]
  usuario_que_modificou = Colaborador.objects.get(id=id_usuario_que_modificou)

  log_Ciclo = LOG_Ciclo.adicionar(ciclo, usuario_que_modificou, 'Criação do ciclo', nome_ciclo , data_final)
  log_Ciclo.save()
  
  ciclo = Ciclo(nome=nome_ciclo, data_inicial=data_inicial, data_final= data_final)
  ciclo.save()

  return JsonResponse({})

@has_role_decorator('administrador')
def alterar_ciclo(requisicao):
  id_ciclo = requisicao.POST["id_ciclo"]
  data_final = requisicao.POST["data_final"]
  id_usuario_que_modificou = requisicao.POST["usuario_que_modificou"]
  novo_nome_ciclo = requisicao.POST["novo_nome_ciclo"]
  descricao_da_alteracao = requisicao.POST["descricao_da_alteracao"]
  ciclo = Ciclo.objects.get(id = id_ciclo)
  usuario_que_modificou = Colaborador.objects.get(id=id_usuario_que_modificou)

  log_Ciclo = LOG_Ciclo.adicionar(ciclo, usuario_que_modificou, descricao_da_alteracao, novo_nome_ciclo, data_final)
  log_Ciclo.save()

  ciclo.alterar_ciclo(data_final,novo_nome_ciclo)
  ciclo.save()
  return JsonResponse({})
  
@has_role_decorator('administrador')
def obter_informacoes_ciclo(requisicao):
  ciclo_atual = obter_ciclo_atual()
  ciclo_futuro = obter_ciclo_futuro()
  log = LOG_Ciclo.objects.filter(ciclo=ciclo_atual).order_by('-data_da_modificacao').first()
  colaborador = Colaborador.objects.get(id=log.usuario_que_modificou.id)
  data_inicial_futura = ciclo_atual.data_final + timedelta(days=1)
  restante_de_dias = data_inicial_futura - date.today()
  
  ciclo_atual = {
    'id_ciclo_atual': ciclo_atual.id,
    'nome_do_ciclo_atual': ciclo_atual.nome,
    'data_inicial_atual': ciclo_atual.data_inicial,
    'data_inicial_formatada_atual': ciclo_atual.data_inicial.strftime('%d/%m/%Y'),
    'data_final_atual': ciclo_atual.data_final,
    'data_final_formatada_atual': ciclo_atual.data_final.strftime('%d/%m/%Y'),
    'nome_usuario_que_modificou_atual': colaborador.nome_abreviado,
    'descricao_da_alteracao_atual': log.descricao_da_alteracao,
    'data_ultima_alteracao_atual': log.data_da_modificacao.strftime('%d/%m/%Y'),
    'porcentagem_do_progresso_atual': ciclo_atual.calcular_porcentagem_progresso(),
  }
  if ciclo_futuro != None:
    ciclo_futuro = {
      'id_ciclo_futuro': ciclo_futuro.id,
      'nome_do_ciclo_futuro': ciclo_futuro.nome,
      'data_inicial_futuro': data_inicial_futura,
      'data_inicial_formatada_futuro': data_inicial_futura.strftime('%d/%m/%Y'),
      'data_final_futuro': ciclo_futuro.data_final,
      'data_final_formatada_futuro': ciclo_futuro.data_final.strftime('%d/%m/%Y'),
      'nome_usuario_que_modificou_futuro': colaborador.nome_abreviado,
      'porcentagem_do_progresso_futuro': ciclo_futuro.calcular_porcentagem_progresso(),
      'tempo_restante_de_dias' : restante_de_dias.days
    }

  else:
    resposta2 = None
  
  resposta = {
    'ciclo_atual': ciclo_atual,
    'ciclo_futuro': ciclo_futuro
  }
  
  return JsonResponse(resposta)

@has_role_decorator('administrador')
def ciclos_passados(requisicao):
  ciclos_passados = map(lambda ciclo: { 
    'id_ciclo': ciclo.id, 
    'nome': ciclo.nome, 
    'nome_autor': obter_nome_usuario_que_modificou(ciclo), 
    'data_inicial': ciclo.data_inicial.strftime('%d/%m/%Y'), 
    'data_final': ciclo.data_final.strftime('%d/%m/%Y') 
    }, obter_ciclos_passados().order_by('-id'))

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

@has_role_decorator('administrador')
def historico_alteracoes(requisicao):
  historico_alteracoes = map(lambda LOG_Ciclo: { 
    'antigo_nome_do_ciclo': LOG_Ciclo.antigo_nome_ciclo, 
    'nome_autor': LOG_Ciclo.usuario_que_modificou.nome_abreviado, 
    'data_anterior': LOG_Ciclo.antiga_data_final.strftime('%d/%m/%Y'), 
    'nova_data': LOG_Ciclo.nova_data_alterada.strftime('%d/%m/%Y'), 
    'data_alteracao': LOG_Ciclo.data_da_modificacao.strftime('%d/%m/%Y'), 
    'motivo_alteracao': LOG_Ciclo.descricao_da_alteracao, 
    'novo_nome_ciclo' : LOG_Ciclo.novo_nome_ciclo
  }, obter_historico_de_alteracoes().order_by('-id'))

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

def obter_ciclo_atual():
  return Ciclo.objects.get(data_final__gte=date.today(), data_inicial__lte=date.today())

def obter_ciclo_futuro():
  ciclo_atual = obter_ciclo_atual()
  return Ciclo.objects.filter(data_inicial__gte=ciclo_atual.data_final).first()

def obter_ciclos_passados():
  return Ciclo.objects.filter(data_final__lte=date.today())

def obter_nome_usuario_que_modificou(ciclo):
  log = LOG_Ciclo.objects.get(ciclo=ciclo.id)
  colaborador = Colaborador.objects.get(id=log.usuario_que_modificou.id)
  return colaborador.nome_abreviado

def obter_historico_de_alteracoes():
  log = LOG_Ciclo.objects.all()
  return log
  
@has_role_decorator('administrador')
def ranking_por_periodo(requisicao):
    data_inicio = requisicao.POST['data_inicio']
    data_fim = requisicao.POST['data_fim']
    
    colaboradores = Colaborador.objects.all()

    transformacao = lambda colaborador : { 
      'nome' : colaborador.nome_abreviado,
      'todos_reconhecimentos' : len(colaborador.reconhecimentos_por_data(converterData(data_inicio), converterData(data_fim))),
      'reconhecimentos_feitos' : len(colaborador.reconhecimentos_feitos_por_data(converterData(data_inicio), converterData(data_fim))),
      'colaborar_sempre': len(colaborador.reconhecimentos_por_pilar_ranking(Pilar.objects.get(nome = "Colaborar sempre"), colaborador.reconhecimentos_por_data(converterData(data_inicio), converterData(data_fim)))),
      'focar_nas_pessoas': len(colaborador.reconhecimentos_por_pilar_ranking(Pilar.objects.get(nome = "Focar nas pessoas"), colaborador.reconhecimentos_por_data(converterData(data_inicio), converterData(data_fim)))),
      'fazer_diferente': len(colaborador.reconhecimentos_por_pilar_ranking(Pilar.objects.get(nome = "Fazer diferente"), colaborador.reconhecimentos_por_data(converterData(data_inicio), converterData(data_fim)))),
      'planejar_entregar_aprender': len(colaborador.reconhecimentos_por_pilar_ranking(Pilar.objects.get(nome = "Planejar, entregar e aprender"), colaborador.reconhecimentos_por_data(converterData(data_inicio), converterData(data_fim)))),
      'foto': colaborador.foto
    }
    
    colaboradores = map(transformacao, colaboradores)

    colaboradoresOrdenados = sorted(colaboradores, key=lambda x: x["todos_reconhecimentos"], reverse=True)
    
    return JsonResponse({'colaboradores': list(colaboradoresOrdenados)})

def converterData(data):
  return datetime.strptime(data, "%Y-%m-%d").date()



