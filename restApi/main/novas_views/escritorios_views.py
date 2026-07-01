from rest_framework import viewsets
from ..serializers import EscritoriosSerializer
from .services import EscritorioService
from .pagination_views import StandardResultsSetPagination
from .permissions import OnlyAdminDELETE


class EscritoriosViewSet(viewsets.ModelViewSet):
    service = EscritorioService()

    serializer_class = EscritoriosSerializer
    permission_classes = [OnlyAdminDELETE]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return self.service.obter_queryset()