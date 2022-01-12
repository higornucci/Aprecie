﻿define([
	'director',
	'app/servicos/servicoDeAutenticacao'
], function (Router, servicoDeAutenticacao) {
	'use strict';

	var router;
	var roteador = {};
	var _controllerAtivo;

	roteador.configurar = function () {
		var rotas = {
			'/': [middlewareDeTransicaoDeTela, limparTela, login],
			'/login': [middlewareDeAutenticacao, middlewareDeAtualizacaoComGoogleAnalytics, middlewareDeToolbar, middlewareDeTransicaoDeTela, limparTela, login],
			'/paginaInicial': [middlewareDeAutenticacao, middlewareDeAtualizacaoComGoogleAnalytics, middlewareDeToolbar, middlewareDeTransicaoDeTela, limparTela, paginaInicial],
			'/estatisticas': [middlewareDeAutenticacao, middlewareDeAtualizacaoComGoogleAnalytics, middlewareDeToolbar, middlewareDeTransicaoDeTela, limparTela, estatisticas],
			'/perfil/:colaboradorId': [middlewareDeAutenticacao, middlewareDeAtualizacaoComGoogleAnalytics, middlewareDeToolbar, middlewareDeTransicaoDeTela, limparTela, perfil],
			'/ranking': [middlewareDeBotaoReconhecer, middlewareDeAutenticacao, middlewareDeAtualizacaoComGoogleAnalytics, middlewareDeToolbar, middlewareDeTransicaoDeTela, limparTela, ranking],
			'/gerenciadorDeCiclos': [middlewareDeAutenticacao, middlewareDeAtualizacaoComGoogleAnalytics, middlewareDeToolbar, middlewareDeTransicaoDeTela, limparTela, gerenciadorDeCiclos]
		};

		function limparTela() {
			$('#conteudo').empty();
		}

		function login() {
			require(['app/login/controller'], function (loginController) {
				_controllerAtivo = loginController;
				loginController.exibir();
			});
		}

		function paginaInicial() {
			require(['app/paginaInicial/controller'], function (controller) {
				_controllerAtivo = controller;
				controller.exibir();
			});
		}

		function estatisticas() {
			require(['app/estatisticas/controller'], function (controller) {
				_controllerAtivo = controller;
				controller.exibir();
			});
		}

		function perfil(colaboradorId) {
			require(['app/perfil/controller'], function (controller) {
				_controllerAtivo = controller;
				controller.exibir(parseInt(colaboradorId));
			});
		}
		
		function ranking() { 
			require(['app/ranking/controller'], function (controller) {
				_controllerAtivo = controller;
				controller.exibir();
			});
		}

		function gerenciadorDeCiclos() {
			require(['app/gerenciadordeCiclos/controller'], function (controller) {
				_controllerAtivo = constroller;
				controller.exibir();
			});
		}

		router = Router(rotas);
		router.init();
	};

	roteador.navegarPara = function (endereco) {
		window.location = '#' + endereco;
	};

	roteador.paginaAtual = function () {
		var endereco = window.location.toString();
		var posicaoDaRota = endereco.indexOf('#') + 1;

		if (posicaoDaRota === 0)
			return '';

		return endereco.substring(posicaoDaRota);
	};

	roteador.atualizar = function () {
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
		require(['app/toolbar/toolbar'], function (toolbar) {
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

	function middlewareDeBotaoReconhecer(){
		require(['app/botaoReconhecer/botaoReconhecer'], function(botaoReconhecer) { 
			if (servicoDeAutenticacao.jaEstaAutenticado() && roteador.paginaAtual() !== '/login') {
				botaoReconhecer.exibir();
				$('body').removeClass('body-login').addClass('body-app');
			}
			else {
				botaoReconhecer.esconder();
				$('body').removeClass('body-app').addClass('body-login');
			}
		});
	}

	function middlewareDeAtualizacaoComGoogleAnalytics() {
		var posicaoDaPrimeiraBarraDaUrl = roteador.paginaAtual().substring(1).indexOf('/');
		var enderecoSemParametrosDeUrl = posicaoDaPrimeiraBarraDaUrl === -1
			? roteador.paginaAtual()
			: roteador.paginaAtual().substring(0, posicaoDaPrimeiraBarraDaUrl + 1);

		var ga = window.ga;

		if (!ga)
			return true;

		ga('set', 'page', enderecoSemParametrosDeUrl);
		ga('send', 'pageview');
	}

	return roteador;
});
