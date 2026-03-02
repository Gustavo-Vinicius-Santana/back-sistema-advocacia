from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from main.serializers import ClienteSerializer, ClienteEsperaSerializer
from rest_framework.pagination import PageNumberPagination
from main.models import Cliente, ClienteEspera
from rest_framework.views import APIView

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from rest_framework.exceptions import ValidationError

class standardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = standardResultsSetPagination
    
    def list(self, request, *args, **kwargs):
        dataAtual = timezone.now().date()

        # Intervalo para quem está dentro de ±5 dias de completar 65 anos
        data65 = dataAtual - relativedelta(years=65)
        dataInicio = data65 - relativedelta(days=5)
        dataFim = data65 + relativedelta(days=5)

        # Adicione as anotações para contar processos por categoria
        queryset = self.get_queryset().annotate(
            prioridade=Case(
                When(
                    dataNascimento__range=(dataInicio, dataFim),
                    then=Value(1)
                ),
                default=Value(0),
                output_field=IntegerField()
            ),
            # Total de processos ativos
            processos_ativos_count=Count(
                'processo',
                filter=Q(processo__status='ativo')
            ),
            # Total de processos arquivados
            processos_arquivados_count=Count(
                'processo',
                filter=Q(processo__status='arquivado')
            ),
            # Total de processos urgentes (ativos e prioritários)
            processos_urgentes_count=Count(
                'processo',
                filter=Q(processo__status='ativo') & 
                       Q(processo__prioritario=True)
            ),
            # Total geral de processos (todas as categorias)
            processos_total_count=Count('processo')
        ).order_by('-prioridade', 'id')
        
        # Filtro por contrato (novo parâmetro)
        contrato_param = request.query_params.get('contrato')
        if contrato_param is not None:
            if contrato_param.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(contrato=True)
            elif contrato_param.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(contrato=False)
            else:
                return Response({"error": "Valor inválido para o parâmetro 'contrato'. Use 'true' ou 'false'."}, status=400)
        
        # Parâmetros de filtro e ordenação
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')

        allowed_fields = [
            'nome','cpf','telefone','inss','parceiro'
        ]
        
        if field and value:
            if field not in allowed_fields:
                return Response({"error": "Campo de filtro inválido."}, status=400)

            # Campos simples
            if field in ['nome', 'cpf', 'telefone', 'inss']:
                queryset = queryset.filter(**{f"{field}__icontains": value})

            # Campo composto (parceiro)
            elif field == 'parceiro':
                queryset = queryset.filter(parceiro__nome__icontains=value)
        
        if order_by:
            if order_by == 'parceiro':
                queryset = queryset.order_by('parceiro__nome')
            else:
                queryset = queryset.order_by(order_by)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            
            # Calcular dias para 65 anos manualmente para cada cliente
            for item in response.data['results']:
                if item.get('dataNascimento'):
                    # Parse da data de nascimento
                    data_nasc_str = item['dataNascimento']
                    # Pode vir em diferentes formatos dependendo do serializer
                    if isinstance(data_nasc_str, str):
                        data_nasc = datetime.strptime(data_nasc_str, '%Y-%m-%d').date()
                    else:
                        # Se já for um objeto date
                        data_nasc = data_nasc_str
                    
                    # Calcular data de 65 anos
                    data_65 = data_nasc + relativedelta(years=65)
                    
                    # Calcular dias restantes
                    dias_para_65 = (data_65 - dataAtual).days
                    item['dias_para_65'] = dias_para_65
                else:
                    item['dias_para_65'] = None
            return response

        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        
        # Calcular dias para 65 anos para resposta sem paginação
        for item in data:
            if item.get('dataNascimento'):
                data_nasc_str = item['dataNascimento']
                if isinstance(data_nasc_str, str):
                    data_nasc = datetime.strptime(data_nasc_str, '%Y-%m-%d').date()
                else:
                    data_nasc = data_nasc_str
                
                data_65 = data_nasc + relativedelta(years=65)
                dias_para_65 = (data_65 - dataAtual).days
                item['dias_para_65'] = dias_para_65
            else:
                item['dias_para_65'] = None
                
        return Response(data)
    
    
class ClienteEsperaViewSet(viewsets.ModelViewSet):
    queryset = ClienteEspera.objects.all()
    serializer_class = ClienteEsperaSerializer
    permission_classes = [IsAuthenticated]


class BuscarClienteCamposView(APIView):
    permission_classes = [IsAuthenticated]
    alowed_field = ['nome','cpf','telefone','inss','parceiro']
    pagination_class = standardResultsSetPagination
    def get(self, request):
        field = request.query_params.get('field')
        value = request.query_params.get('value')
        order_by = request.query_params.get('order_by')
        
        if not field or not value: 
            raise ValueError({
                "error": "Os campos 'field' e 'value' são obrigatórios."
            })
        if field not in self.alowed_field:
            raise ValueError({
                "error": f"O campo '{field}' não é permitido para busca."
            })
        if not order_by:
            if field == 'parceiro':
                queryset = Cliente.objects.filter(
                    parceiro__nome__icontains=value
                ).order_by('id')  
            else:     
                queryset = Cliente.objects.filter(**{f"{field}__contains": value}).order_by('id')
        else:
            if field == 'parceiro':
                queryset = Cliente.objects.filter(
                    parceiro__nome__icontains=value
                ).order_by(order_by)
            else:
                queryset = Cliente.objects.filter(**{f"{field}__contains": value}).order_by(order_by)
        return Response(ClienteSerializer(queryset, many=True).data)



class ClientesSemContratoView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        dataAtual = timezone.now().date()

        field = request.GET.get('field')
        value = request.GET.get('value')
        order_by = request.GET.get('order_by')

        page = request.GET.get('page', 1)
        page_size = int(request.GET.get('page_size', 10))

        allowed_field = ['nome', 'dataNascimento', 'sexo', 'email', 'telefone']

        # Validando o campo
        if field and value:
            if field not in allowed_field:
                raise ValidationError({
                    'error': f'O campo "{field}" nao é permitido para busca.'
                })
            # Query filtrando clientes sem contrato 
            clientes = Cliente.objects.filter(
                contrato = False
            ).filter(
                **{f"{field}__icontains": value}
            )
        else:
            # Query base
            clientes = Cliente.objects.filter(
                contrato = False
            )

            

        # intervalo de nascimentos para quem fará 65 anos em até 5 dias
        data65 = dataAtual - relativedelta(years=65)
        dataInicio = data65 - relativedelta(days=5)  # já fez (até 5 dias atrás)
        dataFim = data65 + relativedelta(days=5) 

        # aplicando prioridades
        clientes = clientes.annotate(
            prioridade=Case(
                When(
                    dataNascimento__range=(dataInicio, dataFim),
                    then=Value(1)
                ),
                default=Value(0),
                output_field=IntegerField()
            )
        )

        # Ordenação final
        if order_by:
            clientes = clientes.order_by('-prioridade', order_by)
        else:
            clientes = clientes.order_by('-prioridade', 'id')
            
        # Paginação
        paginator = Paginator(clientes, page_size)
        try:
            clientes = paginator.page(page)
        except PageNotAnInteger:
            clientes = paginator.page(1)
        except EmptyPage:
            clientes = paginator.page(paginator.num_pages)

        # Serialização
        serializer = ClienteSerializer(clientes, many=True)
        jsonFile = serializer.data
        return JsonResponse(jsonFile, safe=False)
    

class ClienteEsperaAdvView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, advogado_id):
        if not advogado_id:
            return JsonResponse({'error':'O ID do advogado é obrigatório.'})
        try:
            clientesEsperaAdv = []
            clientesEspera = ClienteEspera.objects.filter(IdAdvogado=advogado_id)
            for cliente in clientesEspera:
                cliente_data = {
                    'id': cliente.id,
                    'nome': cliente.nome,
                    'telefone': cliente.telefone,
                    'observacoes': cliente.observacoes,
                    'IdAdvogado': cliente.IdAdvogado,
                    'cpf': cliente.cpf,
                    'dataNascimento':cliente.dataNascimento
                }
                clientesEsperaAdv.append(cliente_data)
            return JsonResponse(clientesEsperaAdv, safe=False)
        except ClienteEspera.DoesNotExist:
            return JsonResponse({'error': 'Nenhum cliente encontrado.'}, status=404)

#depois preciso criar os urls e testar
#todos os views de Cliente estão agrupados aqui e transformados em POO.