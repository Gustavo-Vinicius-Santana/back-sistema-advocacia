from ...models import Documentos,ArquivoModel, ArquivoTarefa


class DocumentoService:
    
    def obter_queryset_documento(self):
        return Documentos.objects.all()
    
    def obter_queryset_arquivos(self):
        return ArquivoModel.objects.all()
    
    
    def obter_queryset_arquivos_tarefa(self):
        return ArquivoTarefa.objects.all()
    
    
    def obter_arquivo_tarefa_por_id(self, arquivo_id):
        return ArquivoTarefa.objects.filter(id=arquivo_id).first()

        
    def obter_arquivos_por_cliente(self, cliente_id):
        return ArquivoModel.objects.filter(cliente_id=cliente_id)