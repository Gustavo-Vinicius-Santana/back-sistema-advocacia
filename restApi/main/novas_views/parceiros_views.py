from ..models import Parceiros
from ..serializers import ParceirosSerializer
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .pagination_views import StandardResultsSetPagination
from django.db.models import Count

class ParceirosViewSet(viewsets.ModelViewSet):
    queryset = Parceiros.objects.all()
    serializer_class = ParceirosSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        # Annota o queryset base com a contagem de clientes
        queryset = Parceiros.objects.annotate(
            total_clientes=Count('clientes')
        )
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Parâmetros de filtro e ordenação
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')

        # Campos permitidos para busca
        allowed_fields = ['nome', 'email', 'cpf', 'telefone']
        
        # Queryset base com annotate
        queryset = self.get_queryset()
        
        # Filtro por campo e valor
        if field and value:
            if field not in allowed_fields:
                return Response({"error": "Campo de filtro inválido."}, status=400)

            # Campos simples (todos os campos são diretos no modelo Parceiros)
            if field in ['nome', 'email', 'cpf', 'telefone']:
                queryset = queryset.filter(**{f"{field}__icontains": value})
        
        # Ordenação
        if order_by:
            # Permite ordenar por total_clientes também
            if order_by in ['total_clientes', '-total_clientes']:
                queryset = queryset.order_by(order_by)
            else:
                queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('id')
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Sem paginação
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)