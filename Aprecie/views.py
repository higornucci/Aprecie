from Aprecie import settings
from django.shortcuts import render
from Aprecie.base import acesso_anonimo

@acesso_anonimo
def index(requisicao):
	return render(requisicao, 'index.html', dict(eh_debug=not settings.ON_OPENSHIFT))