from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from main.serializers import ClienteSerializer, ClienteEsperaSerializer
from rest_framework.pagination import PageNumberPagination
from main.models import Cliente, ClienteEspera
from rest_framework.views import APIView
import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from .services import ClienteService
from .permissions import *

class standardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [OnlyAdminDELETE]
    pagination_class = standardResultsSetPagination
    
    def get_queryset(self):
        service = ClienteService()
        return service.get_queryset_anotado()
    
    def list(self, request, *args, **kwargs):
        service = ClienteService()
        
        try:
            contrato_param = request.query_params.get('contrato')
            queryset = service.filtrar_e_ordenar(
                field=request.query_params.get('field'),
                value=request.query_params.get('value'),
                order_by=request.query_params.get('order_by'),
                contrato=contrato_param
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            
            for item in response.data['results']:
                data_nasc = item.get('dataNascimento')
                if data_nasc:
                    if isinstance(data_nasc, str):
                        #está dessa forma pois importei o módulo datetime
                        data_nasc = datetime.datetime.strptime(data_nasc, '%Y-%m-%d').date()
                    item['dias_para_65'] = service.calcular_dias_para_65_anos(data_nasc)
                else:
                    item['dias_para_65'] = None
            return response

        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        
        for item in data:
            data_nasc = item.get('dataNascimento')
            if data_nasc:
                if isinstance(data_nasc, str):
                    data_nasc = datetime.strptime(data_nasc, '%Y-%m-%d').date()
                item['dias_para_65'] = service.calcular_dias_para_65_anos(data_nasc)
            else:
                item['dias_para_65'] = None
                
        return Response(data)
    
    
class ClienteEsperaViewSet(viewsets.ModelViewSet):
    queryset = ClienteEspera.objects.all()
    serializer_class = ClienteEsperaSerializer
    permission_classes = [OnlyAdminDELETE]


class BuscarClienteCamposView(APIView):
    permission_classes = [OnlyAdminDELETE]
    alowed_field = ['nome','cpf','telefone','inss','parceiro']
    pagination_class = standardResultsSetPagination
    def get(self, request):
        service = ClienteService()
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')
        
        try:
            queryset = service.buscar_por_campo(field, value, order_by)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        
        return Response(ClienteSerializer(queryset, many=True).data)



class ClientesSemContratoView(APIView):
    permission_classes = [OnlyAdminDELETE]

    def get(self, request):
        service = ClienteService()
        
        field = request.GET.get('field')
        value = request.GET.get('value')
        order_by = request.GET.get('order_by')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        try:
            clientes = service.obter_clientes_sem_contrato(field, value, order_by)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        
        paginator = Paginator(clientes, page_size)
        try:
            clientes_page = paginator.page(page)
        except PageNotAnInteger:
            clientes_page = paginator.page(1)
        except EmptyPage:
            clientes_page = paginator.page(paginator.num_pages)

        serializer = ClienteSerializer(clientes_page, many=True)
        return Response(serializer.data)
    

class ClienteEsperaAdvView(APIView):
    permission_classes = [OnlyAdminDELETE]

    def get(self, request, advogado_id):
        service = ClienteService()
        
        try:
            clientes_espera = service.obter_clientes_espera_por_advogado(advogado_id)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        clientes_espera_adv = []
        for cliente in clientes_espera:
            cliente_data = {
                'id': cliente.id,
                'nome': cliente.nome,
                'telefone': cliente.telefone,
                'observacoes': cliente.observacoes,
                'IdAdvogado': cliente.IdAdvogado,
                'cpf': cliente.cpf,
                'dataNascimento': cliente.dataNascimento
            }
            clientes_espera_adv.append(cliente_data)
        
        return JsonResponse(clientes_espera_adv, safe=False)

