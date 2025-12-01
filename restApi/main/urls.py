from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views



router = DefaultRouter()
router.register(r'clientes', views.ClienteViewSet)
router.register(r'advogados', views.AdvogadoViewSet)
router.register(r'processos', views.ProcessoViewSet)
router.register(r'gruposAcao', views.GrupoAcaoViewSet, basename='gruposAcao')
router.register(r'tiposAcao', views.TipoAcaoViewSet, basename='tiposAcao')
router.register(r'fasesProcesso', views.FaseProcessoViewSet, basename='fasesProcesso')
router.register(r'etapasProcesso', views.EtapaProcessoViewSet, basename='etapasProcesso')
router.register(r'tarefas', views.TarefasViewSet)
router.register(r'tipoTarefa', views.TipoTarefaViewSet, basename='tipoTarefa')
router.register(r'clientesEspera', views.ClienteEsperaViewSet,basename='clientesEspera')
router.register(r'documentos', views.DocumentosViewSet,basename='documentos')
router.register(r'representantes', views.RepresentanteViewSet,basename='representantes')
router.register(r'parceiros', views.ParceirosViewSet,basename='parceiros')
router.register(r'escritorios', views.EscritoriosViewSet,basename='escritorios')
router.register(r'arquivoModel', views.ArquivoModelViewSet, basename='arquivoModel')
router.register(r'arquivoTarefa', views.ArquivoTarefaViewSet, basename='arquivoTarefa')

"""BUG 14/07/2025: o endpoint de clientes espera os dados dos clientes ja cadastrados.
Corrigido: em 1 hora"""

"""Dessa forma ai em cima o router do django ja vai criar as views [GET, POST, PUT, DELETE E PATCH]"""

urlpatterns = [
    path('token/', views.CustomTokenObtainPairView.as_view(), name='custom_token_obtain_pair'),
    path('token/resetValidate/<str:token>', views.validate_reset_token_endpoint, name='validate_reset_token_endpoint'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('registrarAdvogado/', views.registrarAdv, name='registrarAdv'),
    path('emailRequestSenha/', views.emailRequestSenha, name='emailRequestSenha'),
    path('resetPassword/<path:token>', views.resetPassword, name='resetPassword'),
    path('cliente/<int:cliente_id>/processos/', views.processosClientes, name='processosClientes'),
    path('clientes/buscar/',views.BuscarClienteCamposView.as_view(), name='buscarClienteCamposView'),
    path('clientesSemContrato/', views.clientesSemContrato, name='clientesSemContrato'),
    #path('clientes65/', views.clientes65, name='clientes65'),
    path('processos/<int:processo_id>/tarefas/', views.tarefasProcesso, name='tarefasProcesso'),
    path('processosConcluidos/<int:processo_id>/', views.processosConcluidosEspecificos, name='processosConcluidosEspecificos'),
    path('processosClientesNome/<str:cliente_nome>/', views.processosClientesNome, name='processosClientesNome'),
    path('BuscarProcessoCampos/',views.BuscarProcessoCampo.as_view(), name='buscarProcessoCamposView'),
    path('advogados/<int:advogado_id>/processos/', views.processosAdvogado, name='processosAdvogado'),
    path('advogados/resumido/', views.advogadosResumido, name= 'advogadosResumido'),
    path('advogados/<int:advogado_id>/dashboard/', views.advogadosDashboard, name= 'advogadosDashboard'),
    path('processos/resumido/', views.processosResumido, name= 'processosResumido'),
    path('tarefas/advogado/<int:advogado_id>/', views.tarefasAdvogadoCriador, name='tarefasAdvogadoCriador'),
    path('advogados/user/',views.advUserInfo, name='advUserInfo'),
    path('advogados/online/', views.AdvogadosOnlineView.as_view(), name='advogadosOnline'),
    path('advogados/<int:advogado_id>/clientesEspera/',views.clientesEsperaAdv, name='clientesEsperaAdv'),
    path('advogados/logout/', views.AdvogadoLogoutView.as_view(), name='advogadosLogout'),
    path('arquivoModel/cliente/<int:cliente>/', views.ArquivoModelClienteIdView.as_view(), name='arquivoModelClienteId'),
    path('arquivoTarefa/tarefa/<int:tarefa>/', views.ArquivoTarefaIdView.as_view(), name='arquivoTarefaTarefaId'),
    path('tarefasConcluidas/<int:tarefa_id>/', views.tarefasConcluidasEspecificas, name='tarefasConcluidasEspecificas'),
    path('historicoTarefas/<int:tarefa_id>/', views.historicoTarefasEspecificos, name='historicoTarefasEspecificos'),
    path('historicoTarefas/', views.historicoTarefas, name='historicoTarefas'),
    path('tarefasDeletadas/',views.tarefasDeletadas, name='tarefasDeletadas'),
    path('tarefasDeletadas/<int:tarefa_id>/',views.tarefasDeletadasEspecificas, name='tarefasDeletadasEspecificas'),
    path('processosArquivados/', views.processosArquivados, name='processosArquivados'),
    path('processosArquivados/<int:processo_id>/', views.processosArquivadosEspecificos, name='processosArquivadosEspecificos'),
    path('graficos/processos/tipo/', views.graficoProcessosTipo, name='graficoProcessosTipo'),
    path('graficos/processos/grupo/', views.graficoProcessosGrupo, name='graficoProcessosGrupo'),
    path('graficos/processos/status/', views.graficoProcessosStatus, name='graficoProcessosStatus'),
    path('graficos/processos/fase/', views.graficosProcessosFase, name='graficosProcessosFase'),
    path('graficos/processos/peticionarProtocolar/', views.graficosProcessosProtocolarPeticionar, name='graficoProcessosPeticionarProtocolar'),
    path('graficos/clientes/contrato/', views.graficoClientesContrato, name='graficoClientesContrato'),
    path('graficos/clientes/parceiro/', views.graficoClientesParceiro, name='graficoClientesParceiro'),
    path('graficos/tarefas/status/', views.graficoTarefasStatus, name='graficoTarefasStatus'),
    path('graficos/tarefas/advogados/', views.graficoTarefasAdvogado, name='graficoTarefasAdvogados'),
    path('etapas/<int:fase_id>/fase/', views.etapasPorFase, name='etapasPorFase'),
    path('tiposAcao/<int:grupo_id>/grupo/', views.tipoPorGrupo, name='tiposAcaoPorGrupo'),
    




    
    path('', include(router.urls)),
    # comentando para teste de commit
]




