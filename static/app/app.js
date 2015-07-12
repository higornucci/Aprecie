var configuracoes = {
	baseUrl: 'static',

	deps: ['app/excecoes/violacaoDeRegra'],

	paths: {
		'text': 'app/lib/requirejs-text/text',
		'jquery': 'app/lib/jquery/dist/jquery',
		'jquery-ui': 'app/lib/jquery-ui/jquery-ui',
		'jquery.inputmask': 'app/lib/jquery.inputmask/dist/jquery.inputmask.bundle',
		'handlebars': 'app/lib/handlebars/handlebars.amd',
		'configuracoes': 'app/configuracoes',
		'growl': 'app/helpers/growl',
		'sessaoDeUsuario': 'app/models/sessaoDeUsuario'
	},

	shim: {
		'jquery': {
			exports: '$'
		},

		'jquery-ui': {
			deps: ['jquery'],
			exports: '$'
		},
		
		'jquery.inputmask':  {
			deps: ['jquery'],
			exports: '$'
		}
	}
};

require.config(configuracoes);

require([
	'configuracoes',
	'app/views/loginView'
], function(configuracoes, loginView) {
	'use strict';

	configuracoes.configurarErros();
	configuracoes.configurarErrosDeRequisicao();
	
	loginView.exibir();
});