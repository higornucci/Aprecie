﻿from django.http import JsonResponse
from django.db.models import Count
from Login.models import Colaborador
from Reconhecimentos.models import Pilar, Reconhecimento, Feedback, Ciclo, LOG_Ciclo
from Reconhecimentos.services import Notificacoes
from django.core.paginator import Paginator
from rolepermissions.decorators import has_role_decorator
from django.db import connection

from datetime import date, datetime

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
    'porcentagem_do_progresso': ciclo.calcular_porcentagem_progresso()
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

def obter_ciclos_passados():
  return Ciclo.objects.filter(data_final__lte=date.today())

def obter_nome_usuario_que_modificou(ciclo):
  log = LOG_Ciclo.objects.get(ciclo=ciclo.id)
  colaborador = Colaborador.objects.get(id=log.usuario_que_modificou.id)
  return colaborador.nome_abreviado

def obter_historico_de_alteracoes():
  log = LOG_Ciclo.objects.all()
  return log

def abreviar_nome(nome):
  return nome.split(' ')[0] + ' ' + nome.split(' ')[-1]

def criar_colaborador(nome, foto):
  return type('',(object,),{
          'nome': abreviar_nome(nome),
          'colaborar_sempre': 0,
          'fazer_diferente': 0,
          'focar_nas_pessoas': 0,
          'planejar_entregar_aprender': 0,
          'todos_reconhecimentos': 0,
          'reconhecimentos_feitos': 0,
          'foto': foto
        })()

def verificar_pilar_colaborador(colaborador, colaborador_transformado):
  id_pilar = colaborador[1]
  quantidade = colaborador[0]
  if id_pilar == 1:
    colaborador_transformado.colaborar_sempre = quantidade
  elif id_pilar == 2:
    colaborador_transformado.fazer_diferente = quantidade
  elif id_pilar == 3:
    colaborador_transformado.focar_nas_pessoas = quantidade
  elif id_pilar == 4:
    colaborador_transformado.planejar_entregar_aprender = quantidade
  
  colaborador_transformado.todos_reconhecimentos += quantidade
  
  return colaborador_transformado

@has_role_decorator('administrador')
def ranking_por_periodo(requisicao):
    data_inicio = requisicao.POST['data_inicio']
    data_fim = requisicao.POST['data_fim']
    
    colaboradores_apreciacoes_recebidas = obter_ranking_de_apreciacoes_recebidas(data_inicio, data_fim)
    colaboradores_apreciacoes_feitas = obter_ranking_de_apreciacoes_feitas(data_inicio, data_fim)
    
    if colaboradores_apreciacoes_recebidas == None and colaboradores_apreciacoes_feitas == None:
      return JsonResponse(status=403, data={'mensagem': 'Não foram encontrados registros para esta data!'})
      
    colaboradores_transformados = []
    colaborador_transformado = None
    for colaborador in colaboradores_apreciacoes_recebidas:      
      if colaborador_transformado == None or colaborador_transformado.nome != colaborador[2]:
        if colaborador_transformado != None:
          colaboradores_transformados.append(colaborador_transformado)
        colaborador_transformado = criar_colaborador(colaborador[2], colaborador[4])
        verificar_pilar_colaborador(colaborador, colaborador_transformado)
      else:
        verificar_pilar_colaborador(colaborador, colaborador_transformado)
      
    colaboradores_transformados.append(colaborador_transformado)

    for colaborador in colaboradores_apreciacoes_feitas:
      colaborador_retornado = busca_colaborador_ranking(colaborador, colaboradores_transformados)
      if colaborador_retornado != None:
        colaborador_retornado.reconhecimentos_feitos = colaborador[0]
      else:
        novo_colaborador = criar_colaborador(colaborador[2], colaborador[3])
        novo_colaborador.reconhecimentos_feitos = colaborador[0]
        colaboradores_transformados.append(novo_colaborador)
    
    colaboradores_ordenados = sorted(colaboradores_transformados, key=lambda x: x.todos_reconhecimentos, reverse=True)

    transformacao = lambda colaborador : { 
       'nome' : colaborador.nome,
       'todos_reconhecimentos' : colaborador.todos_reconhecimentos,
       'colaborar_sempre': colaborador.colaborar_sempre,
       'focar_nas_pessoas': colaborador.focar_nas_pessoas,
       'fazer_diferente': colaborador.fazer_diferente,
       'planejar_entregar_aprender': colaborador.planejar_entregar_aprender,
       'reconhecimentos_feitos' : colaborador.reconhecimentos_feitos,
       'foto': colaborador.foto
     }
    
    colaboradores = map(transformacao, colaboradores_ordenados)

    return JsonResponse({'colaboradores': list(colaboradores)})

def busca_colaborador_ranking(colaborador, colaboradores_transformados):
  for colaborador_transformado in colaboradores_transformados:
    if colaborador[2] == colaborador_transformado.nome:
      return colaborador_transformado
  return None

def obter_ranking_de_apreciacoes_recebidas(data_inicial, data_final):
  with connection.cursor() as cursor:
    cursor.execute('''
    SELECT count(*), r.pilar_id, l.nome, r.reconhecido_id, l.foto
    FROM public."Reconhecimentos_reconhecimento" r
    JOIN public."Login_colaborador" l ON r.reconhecido_id = l.id
    WHERE r.data BETWEEN %s AND %s
    GROUP by l.nome, r.pilar_id, r.reconhecido_id, l.foto
    ORDER by r.reconhecido_id, r.pilar_id
    ''', [data_inicial, data_final])
    
    ranking_de_apreciacoes_recebidas = cursor.fetchall()
  return ranking_de_apreciacoes_recebidas

def obter_ranking_de_apreciacoes_feitas(data_inicial, data_final):
  with connection.cursor() as cursor:
    cursor.execute('''
    SELECT count(*), r.reconhecedor_id, l.nome, l.foto
    FROM public."Reconhecimentos_reconhecimento" r
    JOIN public."Login_colaborador" l ON r.reconhecedor_id = l.id
    WHERE r.data BETWEEN %s AND %s
    GROUP by r.reconhecedor_id, l.nome, l.foto
    ORDER by r.reconhecedor_id
    ''', [data_inicial, data_final])
    ranking_de_apreciacoes_feitas = cursor.fetchall()
  return ranking_de_apreciacoes_feitas
  
def converterData(data):
  return datetime.strptime(data, "%Y-%m-%d").date()