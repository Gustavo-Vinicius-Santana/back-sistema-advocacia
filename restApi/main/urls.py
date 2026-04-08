from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .novas_views import *

router = DefaultRouter()
router.register(r'clientes', views.ClienteViewSet)
router.register(r'advogados', views.AdvogadoViewSet)
router.register(r'processos', views.ProcessoViewSet)
router.register(r'gruposAcao', data_field_views.GrupoAcaoViewSet, basename='gruposAcao')
router.register(r'tiposAcao', data_field_views.TipoAcaoViewSet, basename='tiposAcao')
router.register(r'fasesProcesso', data_field_views.FaseProcessoViewSet, basename='fasesProcesso')
router.register(r'etapasProcesso', data_field_views.EtapaProcessoViewSet, basename='etapasProcesso')
router.register(r'tarefas', views.TarefasViewSet)
router.register(r'tipoTarefa', data_field_views.TipoTarefaViewSet, basename='tipoTarefa')
router.register(r'clientesEspera', views.ClienteEsperaViewSet,basename='clientesEspera')
router.register(r'documentos', views.DocumentosViewSet,basename='documentos')
router.register(r'representantes', views.RepresentanteViewSet,basename='representantes')
router.register(r'parceiros', views.ParceirosViewSet,basename='parceiros')
router.register(r'escritorios', views.EscritoriosViewSet,basename='escritorios')
router.register(r'arquivoModel', views.ArquivoModelViewSet, basename='arquivoModel')
router.register(r'arquivoTarefa', views.ArquivoTarefaViewSet, basename='arquivoTarefa')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', auth_views.CustomTokenObtainPairView.as_view(), name='custom_token_obtain_pair'),
    path('token/resetValidate/<str:token>', auth_views.ValidateResetTokenView.as_view(), name='validate_reset_token_endpoint'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('registrarAdvogado/', advogados_views.AdvogadoRegisterView.as_view(), name='registrarAdv'),
    path('emailRequestSenha/', auth_views.EmailRequestSenha.as_view(), name='emailRequestSenha'),
    path('resetPassword/<path:token>', auth_views.ResetPasswordView.as_view(), name='resetPassword'),
    #path('clientes65/', views.clientes65, name='clientes65'),
    path('processosClientesNome/<str:cliente_nome>/', data_field_views.ProcessosClientesNomeView.as_view(), name='processosClientesNome'), # deve estar no dominio data field
    #mudança no endpoint abaixo, antes era /advogados/advogado_id/dashboard/
    path('advogados/dashboard/<int:advogado_id>/', advogados_views.AdvogadosDashboardView.as_view(), name= 'advogadosDashboard' ),
    path('advogado/current-user/',advogados_views.AdvogadoUserInfoView.as_view(), name='advUserInfo'), #dando erro
    path('advogados/<int:advogado_id>/clientesEspera/',cliente_views.ClienteEsperaAdvView.as_view(), name='clientesEsperaAdv'),
    path('advogados/logout/', advogados_views.AdvogadoLogoutView.as_view(), name='advogadosLogout'),
    path('arquivoModel/cliente/<int:cliente>/', views.ArquivoModelClienteIdView.as_view(), name='arquivoModelClienteId'),
    path('arquivoTarefa/tarefa/<int:tarefa>/', views.ArquivoTarefaIdView.as_view(), name='arquivoTarefaTarefaId'),
    path('historicoTarefas/<int:tarefa_id>/', tarefas_views.HistoricoTarefasEspecificosView.as_view(), name='historicoTarefasEspecificos'),
    path('historicoTarefas/', tarefas_views.HistoricoTarefasView.as_view(), name='historicoTarefas'),
    path('graficos/processos/tipo/', graficos_views.GraficosProcessosTipoView.as_view(), name='graficoProcessosTipo'),
    path('graficos/processos/grupo/', graficos_views.GraficosProcessosGrupoView.as_view(), name='graficoProcessosGrupo'),
    path('graficos/processos/status/', graficos_views.GraficoProcessosStatusView.as_view(), name='graficoProcessosStatus'),
    path('graficos/processos/fase/', graficos_views.GraficosProcessosFaseView.as_view(),name='graficosProcessosFase'),
    path('graficos/processos/peticionarProtocolar/', graficos_views.GraficosProcessosProtocolarPeticionarView.as_view(), name='graficoProcessosPeticionarProtocolar'),
    path('graficos/clientes/contrato/', graficos_views.GraficosClientesContratosView.as_view(), name='graficoClientesContrato'),
    path('graficos/clientes/parceiro/', graficos_views.GraficoClientesParceirosView.as_view(), name='graficoClientesParceiro'),
    path('graficos/tarefas/status/', graficos_views.GraficoTarefasStatusView.as_view(), name='graficoTarefasStatus'),
    path('graficos/tarefas/advogados/', graficos_views.GraficosTarefasAdvogadoView.as_view(), name='graficoTarefasAdvogados'),
    
    path('cliente/<int:cliente_id>/representante/', data_field_views.BuscarRepresentantesPorClienteView.as_view(), name='representante-por-cliente'),
    
    path('select/', views.generic_select_view, name='generic-select'), # deve estar no dominio data field,

    path('search-select/', views.searchSelect, name='search-select'), # deve estar no dominio data field,
]