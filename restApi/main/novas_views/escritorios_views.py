from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..serializers import EscritoriosSerializer
from ..models import Escritorios
from .pagination_views import StandardResultsSetPagination


class EscritoriosViewSet(viewsets.ModelViewSet):
    queryset = Escritorios.objects.all()
    serializer_class = EscritoriosSerializer
    permission_classes = [IsAuthenticated]
    
    # Adicione este atributo - assumindo que standardResultsSetPagination já está definido
    pagination_class = StandardResultsSetPagination
