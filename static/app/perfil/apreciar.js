define([
	"text!app/perfil/apreciarTemplate.html",
	"app/models/reconhecerViewModel",
	"template",
	"growl",
	"roteador",
	"sessaoDeUsuario",
	"app/helpers/formatadorDeData"
], function (
	apreciarTemplate,
	ReconhecerViewModel,
	template,
	growl,
	roteador,
	sessaoDeUsuario,
	formatadorDeData,
) {
	"use strict";

	var _self = {};
	var _sandbox;

	_self.inicializar = function (sandbox, colaboradorId) {
		_sandbox = sandbox;
		_sandbox.escutar("exibir-espaco-para-apreciar", exibir);
	};

	_self.finalizar = function () {
		_sandbox.removerEscuta("exibir-espaco-para-apreciar");
	};

	function exibir(colaboradorId, reconhecimentosDoColaborador) {
		if (sessaoDeUsuario.id === colaboradorId)
			return;
		else {
			template.exibirEm(
				'div[data-js="apreciacao"]',
				apreciarTemplate,
				reconhecimentosDoColaborador
			);

			$("#conteudo")
				.on("click", "div.escrever-apreciacao div.campos", selecionarPilar)
				.on("click", 'button[data-js="reconhecer"]', reconhecer);
		}
	}

	function selecionarPilar() {
		$("div.campos.selecionado").removeClass("selecionado");
		$(this).toggleClass("selecionado").find(":radio").attr("checked", true);
	}

	function reconhecer() {
		$('button[data-js="reconhecer"]').prop("disabled", "disabled");
		obterDataDeReconhecimento();
	}


	function obterDataDeReconhecimento() {
		var dataHoje = formatadorDeData.obterHoje("-");

		$.getJSON(
			"/reconhecimentos/ultima_data_de_publicacao/" + sessaoDeUsuario.id,
			function (dataDePublicacao) {
				if (dataDePublicacao.ultima_data == null || dataDePublicacao.ultima_data < dataHoje) {
					gerarReconhecimento();
				} else if (dataDePublicacao.ultima_data == dataHoje) {
					growl
						.deErro()
						.exibir(
							"Você já fez seu reconhecimento de hoje, amanhã você poderá fazer outro"
						);
					roteador.atualizar();
				}
			}
		);
	}

	function gerarReconhecimento() {
		var reconhecerViewModel = new ReconhecerViewModel();

		try {
			validarOperacao(reconhecerViewModel);
		} catch (erro) {
			$('#conteudo button[data-js="reconhecer"]').removeAttr("disabled");
			throw erro;
		}

		$.post("/reconhecimentos/reconhecer/", reconhecerViewModel, function () {
			growl.deSucesso().exibir("Reconhecimento realizado com sucesso");
			roteador.atualizar();
		}).fail(function () {
			$('#conteudo button[data-js="reconhecer"]').removeAttr("disabled");
		});
	}

	function validarOperacao(reconhecerViewModel) {
		if (!reconhecerViewModel.id_do_pilar)
			throw new ViolacaoDeRegra("O pilar deve ser informado.");

		if (reconhecerViewModel.descritivo === "")
			throw new ViolacaoDeRegra(
				"O reconhecimento precisa ser feito."
			);
	}

	return _self;
});

function mostrarResultado(box,num_max,campospan){
	var contagem_carac = box.length;
	
	if (contagem_carac >= 0){
	document.getElementById(campospan).innerHTML = contagem_carac + "/220";
	}
	if (contagem_carac >= num_max){
	document.getElementById(campospan).innerHTML = "Limite de caracteres excedido!";
	}
   
}
