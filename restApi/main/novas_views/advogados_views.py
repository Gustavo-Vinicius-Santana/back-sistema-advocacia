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

import jwt


class AdvogadoRegisterView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = Advogado.objects.all()

    def post(self, request):
        chave_recebida = request.headers.get(getattr(settings,'API_HEADER_NAME','X-Api-Key'))
        resultado = AdvogadoService.validate_chave_login(chave_recebida)
        if not resultado:
            return JsonResponse({'error': 'Chave de API inválida.'}, status=403)
        data = json.loads(request.body)
        nome = data.get('nome')
        telefone = data.get('telefone')
        email = data.get('email')
        password = data.get('password')
        oab = data.get('oab')
        foto = data.get('foto')  # ✅ novo campo

        if not nome or not email:
            return JsonResponse({"error": "Nome e email são obrigatórios."}, status=400)

        advogado = Advogado.objects.create(
            nome=nome, 
            telefone=telefone,
            email=email,
            oab=oab,
            foto=foto  # ✅ salva a URL da foto
        )
        advogado.set_password(password)
        advogado.save()
        return JsonResponse({'message': 'advogado registrado com sucesso'}, status=201)

class AdvogadoViewSet(viewsets.ModelViewSet):
    queryset = Advogado.objects.all()
    serializer_class = AdvogadoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Retorna queryset com anotações de tarefas via service"""
        service = AdvogadoService()
        return service.get_queryset_anotado()
    
    def list(self, request, *args, **kwargs):
        """Lista advogados com filtro e ordenação delegados ao service"""
        service = AdvogadoService()
        
        try:
            # Delegar lógica de filtro e ordenação ao service
            queryset = service.filtrar_e_ordenar(
                field=request.query_params.get('field'),
                value=request.query_params.get('value'),
                order_by=request.query_params.get('order_by')
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        
        # Aplicar paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class AdvogadosOnlineView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = Advogado.objects.all()

    def get(self, request):
        advogados_online = Advogado.objects.filter(is_online=True)
        serializer = AdvogadoSerializer(advogados_online, many=True)
        return Response(serializer.data)


class AdvogadoLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        service = AdvogadoService()
        try:
            service.atualizar_status_online(request.user.id, is_online=False)
            return Response({"detail": "Logout realizado com sucesso."})
        except ValueError as e:
            return Response({"error": str(e)}, status=404)


class AdvogadosResumidoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        advogados = Advogado.objects.all()
        serializer = AdvogadoResumidoSerializer(advogados, many=True)
        return Response(serializer.data)


class AdvogadosDashboardView(APIView):
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
    permission_classes = [IsAuthenticated]
    queryset = Advogado.objects.all()
    
    def get(self, request, *args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return Response({'error': 'Token nao encontrado.'})
        try:
            formated_token = token.split(' ')[1]
            payload = jwt.decode(formated_token, settings.SECRET_KEY, algorithms=['HS256'])
            advogado_id = payload.get('user_id')
            advogado = Advogado.objects.get(id=advogado_id)
            serializer = AdvogadoSerializer(advogado)
            return Response(serializer.data)
        except IndexError:
            return Response({'error': 'Formato do token inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidTokenError:
            return Response({'error': 'Token inválido ou expirado.'}, status=status.HTTP_401_UNAUTHORIZED)
        except Advogado.DoesNotExist:
            return Response({'error': 'Advogado não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdvogadoRegisterView(APIView):
    """
    Endpoint para registro de advogados.
    Delega validação e criação ao AdvogadoService.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        service = AdvogadoService()
        
        # Validar chave de API
        chave_recebida = request.headers.get(
            getattr(settings, 'API_HEADER_NAME', 'X-Api-Key')
        )
        if not service.validate_chave_login(chave_recebida):
            return JsonResponse(
                {'error': 'Chave de API inválida.'},
                status=403
            )
        
        # Obter dados do request
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "JSON inválido."},
                status=400
            )
        
        # Registrar advogado via service
        try:
            advogado = service.registrar_advogado(
                nome=data.get('nome'),
                email=data.get('email'),
                telefone=data.get('telefone'),
                oab=data.get('oab'),
                foto=data.get('foto'),
                password=data.get('password')
            )
            return JsonResponse(
                {'message': 'Advogado registrado com sucesso'},
                status=201
            )
        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=400
            )


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


class AdvogadoLogoutView(APIView):
    """
    Endpoint de logout.
    Marca o advogado como offline via service.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        service = AdvogadoService()
        try:
            service.atualizar_status_online(
                request.user.id,
                is_online=False
            )
            return Response(
                {"detail": "Logout realizado com sucesso."}
            )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )


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
        token = request.headers.get('Authorization')
        if not token:
            return Response({'error': 'Token não encontrado.'})
        
        try:
            formated_token = token.split(' ')[1]
            payload = jwt.decode(
                formated_token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
            advogado_id = payload.get('user_id')
            advogado = Advogado.objects.get(id=advogado_id)
            serializer = AdvogadoSerializer(advogado)
            return Response(serializer.data)
        except IndexError:
            return Response(
                {'error': 'Formato do token inválido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except InvalidTokenError:
            return Response(
                {'error': 'Token inválido ou expirado.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Advogado.DoesNotExist:
            return Response(
                {'error': 'Advogado não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
