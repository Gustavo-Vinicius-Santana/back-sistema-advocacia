from ...models import Escritorios

class EscritorioService:
    
    def obter_queryset(self):
        return Escritorios.objects.all()