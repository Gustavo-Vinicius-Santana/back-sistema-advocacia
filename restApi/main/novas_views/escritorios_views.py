from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..serializers import EscritoriosSerializer
from .services import EscritorioService
from .pagination_views import StandardResultsSetPagination


class EscritoriosViewSet(viewsets.ModelViewSet):
    service = EscritorioService()
    queryset = service.obter_queryset
    serializer_class = EscritoriosSerializer
    permission_classes = [IsAuthenticated]
    
    # Adicione este atributo - assumindo que standardResultsSetPagination já está definido
    pagination_class = StandardResultsSetPagination
