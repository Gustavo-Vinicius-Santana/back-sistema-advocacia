from django.urls import path, include
from .views import ClienteViewSet, AdvogadoViewSet, ProcessoViewSet
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views



router = DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'advogados', AdvogadoViewSet)
router.register(r'processos', ProcessoViewSet)

"""Dessa forma ai em cima o router do django ja vai criar as views [GET, POST, PUT, DELETE E PATCH]"""

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('registrarAdvogado/', views.registrarAdv, name='registrarAdv'),
    path('emailRequestSenha/', views.emailRequestSenha, name='emailRequestSenha'),
    path('resetPassword/<path:token>', views.resetPassword, name='resetPassword'),
    
]
