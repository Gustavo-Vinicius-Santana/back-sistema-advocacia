from ..models import Advogado
from ..serializers import AdvogadoResumidoSerializer, AdvogadoSerializer
from .services.advogado_services import AdvogadoService
from rest_framework import viewsets, status
from django.conf import settings
from rest_framework.response import Response
from .pagination_views import StandardResultsSetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from jwt.exceptions import InvalidTokenError
import json
from django.http import JsonResponse
from .permissions import *
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

import jwt


class AdvogadosOnlineView(APIView):
    permission_classes = [OnlyAdminDELETE]
    queryset = Advogado.objects.all()

    def get(self, request):
        advogados_online = Advogado.objects.filter(is_online=True)
        serializer = AdvogadoSerializer(advogados_online, many=True)
        return Response(serializer.data)

class AdvogadosResumidoView(APIView):
    permission_classes = [OnlyAdminDELETE]

    def get(self, request):
        advogados = Advogado.objects.all()
        serializer = AdvogadoResumidoSerializer(advogados, many=True)
        return Response(serializer.data)


class AdvogadosDashboardView(APIView):
    permission_classes = [OnlyAdminDELETE]

    def get(self, request, *args, **kwargs):
        service = AdvogadoService()
        try:
            # Delegar lógica ao service
            dashboard_data = service.obter_dashboard(request.user.id)
            return Response(dashboard_data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        
    
class AdvogadoUserInfoView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = Advogado.objects.all()
    
    def get(self, request, *args, **kwargs):
        # With cookie-based authentication, request.user is already populated
        # by the authentication middleware
        try:
            advogado = request.user
            serializer = AdvogadoSerializer(advogado)
            serializer_formatado = dict(serializer.data)
            if advogado.is_staff:
                serializer_formatado['role'] = 'staff'
            elif advogado.is_superuser:
                serializer_formatado['role'] = 'admin'
            else:
                serializer_formatado['role'] = 'advogado'
            return Response(serializer_formatado)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdvogadoRegisterView(APIView):
    """
    Endpoint para registro de advogados.
    Delega validação e criação ao AdvogadoService.
    """
    permission_classes = []

    def post(self, request):
        service = AdvogadoService()
        data = request.data

        
        # Registrar advogado via service
        try:
            advogado = service.registrar_advogado(
                nome=data.get('nome'),
                email=data.get('email'),
                telefone=data.get('telefone'),
                oab=data.get('oab'),
                foto=request.FILES.get('foto') or data.get('foto'),
                is_staff=data.get('is_staff', False),
                password=data.get('password')
            )
            return JsonResponse(
                {'message': 'Advogado registrado com sucesso'},
                status=201
            )
        except ValueError as e:
            raise ValidationError(str(e))


class AdvogadoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar advogados.
    Lógica de filtro/ordenação delegada ao AdvogadoService.
    """
    queryset = Advogado.objects.all()
    serializer_class = AdvogadoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Retorna queryset com anotações de tarefas via service"""
        service = AdvogadoService()
        return service.get_queryset_anotado()
    
    def list(self, request, *args, **kwargs):
        """
        Lista advogados com filtro e ordenação.
        
        Query params:
        - field: campo para filtro (nome, email, telefone, oab)
        - value: valor para filtro
        - order_by: campo para ordenação
        """
        service = AdvogadoService()
        
        try:
            # Delegar lógica de filtro e ordenação ao service
            queryset = service.filtrar_e_ordenar(
                field=request.query_params.get('field'),
                value=request.query_params.get('value'),
                order_by=request.query_params.get('order_by')
            )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aplicar paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AdvogadosOnlineView(APIView):
    """Retorna lista de advogados online"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        advogados_online = Advogado.objects.filter(is_online=True)
        serializer = AdvogadoSerializer(advogados_online, many=True)
        return Response(serializer.data)


@method_decorator(csrf_protect, name='dispatch')
class AdvogadoLogoutView(APIView):
    """
    Endpoint de logout.
    Marca o advogado como offline via service.
    """
    # Logout must also clear stale cookies after the access token expires.
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token:
            try:
                refresh = RefreshToken(refresh_token)
                AdvogadoService().atualizar_status_online(
                    refresh['user_id'],
                    is_online=False,
                )
                refresh.blacklist()
            except (TokenError, ValueError, KeyError):
                # A token may already be expired or revoked. Cookie removal
                # still needs to succeed in this case.
                pass

        response = Response({"detail": "Logout realizado com sucesso."})
        # Deletar cookies - o método delete_cookie do Django não aceita parâmetros como secure/samesite
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        return response


class AdvogadosResumidoView(APIView):
    """Retorna lista resumida de advogados"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        advogados = Advogado.objects.all()
        serializer = AdvogadoResumidoSerializer(advogados, many=True)
        return Response(serializer.data)


class AdvogadosDashboardView(APIView):
    """
    Dashboard do advogado com estatísticas.
    Lógica delegada ao AdvogadoService.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        service = AdvogadoService()
        try:
            # Delegar lógica ao service
            dashboard_data = service.obter_dashboard(request.user.id)
            return Response(dashboard_data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdvogadoUserInfoView(APIView):
    """Retorna informações do usuário autenticado"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        serializer = AdvogadoSerializer(request.user)
        serializer_formatado = dict(serializer.data)
        if request.user.is_staff:
            serializer_formatado['role'] = 'staff'
        elif request.user.is_superuser:
            serializer_formatado['role'] = 'admin'
        else:
            serializer_formatado['role'] = 'advogado'
        return Response(serializer_formatado)
