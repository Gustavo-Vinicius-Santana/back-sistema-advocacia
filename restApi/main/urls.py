from django.urls import path, include
from .views import ClienteViewSet, AdvogadoViewSet, ProcessoViewSet,TarefasViewSet
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views



router = DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'advogados', AdvogadoViewSet)
router.register(r'processos', ProcessoViewSet)
router.register(r'tarefas', views.TarefasViewSet)

"""Dessa forma ai em cima o router do django ja vai criar as views [GET, POST, PUT, DELETE E PATCH]"""

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('registrarAdvogado/', views.registrarAdv, name='registrarAdv'),
    path('emailRequestSenha/', views.emailRequestSenha, name='emailRequestSenha'),
    path('resetPassword/<path:token>', views.resetPassword, name='resetPassword'),
    path('cliente/<int:cliente_id>/processos/', views.processosClientes, name='processosClientes'),
    path('processos/<int:processo_id>/tarefas/', views.tarefasProcesso, name='tarefasProcesso'),
    path('advogados/<int:advogado_id>/processos/', views.processosAdvogado, name='processosAdvogado'),
    path('advogados/resumido', views.advogadosResumido, name= 'advogadosResumido'),
    path('processos/resumido', views.processosResumido, name= 'processosResumido'),
    
]
