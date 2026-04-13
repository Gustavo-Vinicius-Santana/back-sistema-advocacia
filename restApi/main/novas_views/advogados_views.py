from ..models import Advogado,Tarefas,Processo
from ..serializers import AdvogadoResumidoSerializer, AdvogadoSerializer
from .services import AdvogadoService
from rest_framework import viewsets,status
from django.db.models import Count, Q
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
    AdvogadoService = AdvogadoService(repository=None)  # Você pode passar um repositório real aqui se necessário
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
    pagination_class = StandardResultsSetPagination  # Adiciona a paginação aqui
    # ToDo Refactor: transformar em service
    def get_queryset(self):
        """
        Annota o queryset base com as contagens de tarefas.
        """
        queryset = Advogado.objects.annotate(
            tarefas_criadas=Count(
                'advogadoCriador__id',
                distinct=True,
                filter=Q(advogadoCriador__deletada=False)
            ),
            tarefas_responsavel=Count(
                'advogadoResponsavel__id',
                distinct=True,
                filter=Q(advogadoResponsavel__deletada=False)
            )
        )
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Parâmetros de filtro e ordenação
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')

        # Campos permitidos para busca
        allowed_fields = ['nome', 'email', 'telefone', 'oab']
        
        # Queryset base com annotate
        queryset = self.get_queryset()
        
        # Filtro por campo e valor
        if field and value:
            if field not in allowed_fields:
                return Response({"error": "Campo de filtro inválido."}, status=400)

            # Campos simples
            if field in ['nome', 'email', 'telefone', 'oab']:
                queryset = queryset.filter(**{f"{field}__icontains": value})
        
        # Ordenação
        if order_by:
            # Permite ordenar pelos campos annotados também
            annotate_fields = [
                'tarefas_criadas', '-tarefas_criadas',
                'tarefas_responsavel', '-tarefas_responsavel'
            ]
            
            if order_by in annotate_fields:
                queryset = queryset.order_by(order_by)
            else:
                queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('id')
        
        # Paginação - EXATAMENTE IGUAL À VIEW DE PARCEIROS
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Sem paginação
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
    queryset = Advogado.objects.all()

    def post(self, request):
        user = request.user
        user.is_online = False
        user.save()
        return Response({"detail": "Logout realizado com sucesso."})
        #implementar o logout baseado no tempo do Token JWT


class AdvogadosResumidoView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = Advogado.objects.all()

    def get(self, request):
        advogados = Advogado.objects.all()
        serializer = AdvogadoResumidoSerializer(advogados, many=True)
        jsonFile = serializer.data
        return Response(jsonFile)


class AdvogadosDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            advogado = request.user

            # Tarefas do advogado
            tarefas = Tarefas.objects.filter(advogadoResponsavelId=advogado.id)

            tarefasConcluidas = tarefas.filter(concluida=True).count()
            tarefasPendentes = tarefas.filter(concluida=False).count()

            # Processos
            processosAtivos = Processo.objects.filter(
                advogadoCriadorId=advogado.id,
                status='ativo'
            ).exclude(concluido=True).count()

            processosConcluidos = Processo.objects.filter(
                advogadoCriadorId=advogado.id,
                concluido=True
            ).count()

            return Response({
                'tarefasConcluidas': tarefasConcluidas,
                'tarefasPendentes': tarefasPendentes,
                'processosAtivos': processosAtivos,
                'processosConcluidos': processosConcluidos,
            })

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
