from  django.conf import settings
from django.http import JsonResponse

class AuthCustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        chave_recebida = request.headers.get(getattr(settings,'API_HEADER_NAME','X-Api-Key'))
        
        if chave_recebida != getattr(settings,'API_SECRET_KEY',"DEFAULT_SECRET"): 
            return JsonResponse({'error':'Chave de API inválida.'},status=403)

        return self.get_response(request) 