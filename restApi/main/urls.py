from django.urls import path, include
from .views import ClienteViewSet, AdvogadoViewSet, ProcessoViewSet,TarefasViewSet,AdvogadosOnlineView,CustomTokenObtainPairView,AdvogadoLogoutView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from django.conf import settings
from django.conf.urls.static import static



router = DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'advogados', AdvogadoViewSet)
router.register(r'processos', ProcessoViewSet)
router.register(r'tarefas', views.TarefasViewSet)
router.register(r'clientesEspera', views.ClienteEsperaViewSet,basename='clientesEspera')

"""BUG 14/07/2025: o endpoint de clientes espera os dados dos clientes ja cadastrados.
Corrigido: em 1 hora"""

"""Dessa forma ai em cima o router do django ja vai criar as views [GET, POST, PUT, DELETE E PATCH]"""

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='custom_token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('registrarAdvogado/', views.registrarAdv, name='registrarAdv'),
    path('emailRequestSenha/', views.emailRequestSenha, name='emailRequestSenha'),
    path('resetPassword/<path:token>', views.resetPassword, name='resetPassword'),
    path('cliente/<int:cliente_id>/processos/', views.processosClientes, name='processosClientes'),
    path('processos/<int:processo_id>/tarefas/', views.tarefasProcesso, name='tarefasProcesso'),
    path('advogados/<int:advogado_id>/processos/', views.processosAdvogado, name='processosAdvogado'),
    path('advogados/resumido/', views.advogadosResumido, name= 'advogadosResumido'),
    path('advogados/<int:advogado_id>/dashboard/', views.advogadosDashboard, name= 'advogadosDashboard'),
    path('processos/resumido/', views.processosResumido, name= 'processosResumido'),
    path('tarefas/advogado/<int:advogado_id>/', views.tarefasAdvogadoCriador, name='tarefasAdvogadoCriador'),
    path('advogados/user/',views.advUserInfo, name='advUserInfo'),
    path('advogados/online/', AdvogadosOnlineView.as_view(), name='advogadosOnline'),
    path('advogados/<int:advogado_id>/clientesEspera/',views.clientesEsperaAdv, name='clientesEsperaAdv'),
    path('advogados/logout/', AdvogadoLogoutView.as_view(), name='advogadosLogout'),
    path('tarefasConcluidas/<int:tarefa_id>/', views.tarefasConcluidasEspecificas, name='tarefasConcluidasEspecificas'),
    path('', include(router.urls)),
    
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


