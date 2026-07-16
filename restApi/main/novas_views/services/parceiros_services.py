from ...models import Parceiros
from django.db.models import Count
class ParceirosService:

    def obter_queryset(self)->Parceiros:
        return Parceiros.objects.all()
    
    def obter_queryset_anotado(self)->Parceiros:
        return Parceiros.objects.annotate(total_clientes=Count('clientes'))

    def list_service(self, request)->Parceiros:
        # Parâmetros de filtro e ordenação
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')

        # Campos permitidos para busca
        allowed_fields = ['nome', 'email', 'cpf', 'telefone']
        
        # Queryset base com annotate
        queryset = self.obter_queryset_anotado()
        
        # Filtro por campo e valor
        if field and value:
            if field not in allowed_fields:
                raise ValueError("Campo de filtro inválido.")

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
        
        return queryset