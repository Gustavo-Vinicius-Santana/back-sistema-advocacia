from ..serializers import ParceirosSerializer
from rest_framework.response import Response
from rest_framework import viewsets
from .pagination_views import StandardResultsSetPagination
from .services import ParceirosService
from .permissions import *


#Novas views chamando os Services para obter os dados e retornar o JsonResponse para os gráficos do frontend.
class ParceirosViewSet(viewsets.ModelViewSet):
    service = ParceirosService()
    queryset = service.obter_queryset()    
    serializer_class = ParceirosSerializer
    permission_classes = [OnlyAdminDELETE]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        # Annota o queryset base com a contagem de clientes
        service = ParceirosService()
        queryset = service.obter_queryset_anotado()
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Parâmetros de filtro e ordenação
        service = ParceirosService()
        try:
            queryset = service.list_service(request)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Sem paginação
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)