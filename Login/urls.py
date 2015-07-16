from django.conf.urls import include, url
from Login import views

urlpatterns = [
    url(r'^entrar/$', views.entrar, name="entrar"),
    url(r'^alterar_foto/$', views.alterar_foto, name="alterar_foto"),
	url(r'^obter_funcionarios/$', views.obter_funcionarios, name="obter_funcionarios"),
]