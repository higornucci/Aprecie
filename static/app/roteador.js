﻿define([
  'director',
  'app/servicos/servicoDeAutenticacao'
], function(Router, servicoDeAutenticacao) {
  'use strict';

  var router;
  var roteador = {};
  var _controllerAtivo;

  roteador.configurar = function() {
    var rotas = {
      '/': [middlewareDeTransicaoDeTela, limparTela, login],
      '/login': [middlewareDeAutenticacao, middlewareDeToolbar, middlewareDeTransicaoDeTela, limparTela, login],
      '/paginaInicial': [middlewareDeAutenticacao, middlewareDeToolbar, middlewareDeTransicaoDeTela, limparTela, paginaInicial],
      '/estatisticas': [middlewareDeAutenticacao, middlewareDeToolbar, middlewareDeTransicaoDeTela, limparTela, estatisticas],
      '/perfil/:colaboradorId': [middlewareDeAutenticacao, middlewareDeToolbar, middlewareDeTransicaoDeTela, limparTela, perfil],
      '/reconhecimentos/:colaboradorId/:valorId': [middlewareDeAutenticacao, middlewareDeToolbar, middlewareDeTransicaoDeTela, limparTela, reconhecimentos]
    };

    function limparTela() {
      $('#conteudo').empty();
    }

    function login() {
      require(['app/login/controller'], function(loginController) {
        _controllerAtivo = loginController;
        loginController.exibir();
      });
    }

    function paginaInicial() {
      require(['app/paginaInicial/controller'], function(controller) {
        _controllerAtivo = controller;
        controller.exibir();
      });
    }

    function estatisticas() {
      require(['app/estatisticas/controller'], function(controller) {
        _controllerAtivo = controller;
        controller.exibir();
      });
    }

    function perfil(colaboradorId) {
      require(['app/perfil/controller'], function(controller) {
        _controllerAtivo = controller;
        controller.exibir(parseInt(colaboradorId));
      });
    }

    function reconhecimentos(colaboradorId, valorId) {
      require(['app/reconhecimentos/controller'], function(controller) {
        _controllerAtivo = controller;
        controller.exibir(parseInt(colaboradorId), parseInt(valorId));
      });
    }

    router = Router(rotas);
    router.init();
  };

  roteador.navegarPara = function(endereco) {
    window.location = '#' + endereco;
  };

  roteador.paginaAtual = function() {
    var endereco = window.location.toString();
    var posicaoDaRota = endereco.indexOf('#') + 1;

    if (posicaoDaRota === 0)
      return '';

    return endereco.substring(posicaoDaRota);
  };

  roteador.atualizar = function() {
    var rotaAntiCache = roteador.paginaAtual() + '?' + new Date().getTime();
    router.setRoute(rotaAntiCache);
  };

  function middlewareDeAutenticacao() {
    if (roteador.paginaAtual() === '/login' && !servicoDeAutenticacao.jaEstaAutenticado())
      return true;

    if (!servicoDeAutenticacao.jaEstaAutenticado()) {
      window.location.href = '/';
      return false;
    }

    servicoDeAutenticacao.atualizarSessaoDeUsuario();
  }

  function middlewareDeTransicaoDeTela() {
    if (_controllerAtivo)
      _controllerAtivo.finalizar();
  }

  function middlewareDeToolbar() {
    require(['app/toolbar/toolbar'], function(toolbar) {
      if (servicoDeAutenticacao.jaEstaAutenticado() && roteador.paginaAtual() !== '/login') {
        toolbar.exibir();
        $('body').removeClass('body-login').addClass('body-app');
      }
      else {
        toolbar.esconder();
        $('body').removeClass('body-app').addClass('body-login');
      }
    });
  }

  return roteador;
});
