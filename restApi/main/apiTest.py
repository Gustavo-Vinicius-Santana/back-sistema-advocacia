import requests

#farei os testes aqui
class ApiTest:
    def __init__(self,url):
        self.url = url
        
    def get(self):
        return requests.get(self.url)
    
    def clientePost(self,dados):
        return requests.post(self.url,data=dados)


    def clienteDelete(self,id):
        return requests.delete(self.url+str(id))

test = ApiTest("http://127.0.0.1:8000/api/clientes/")
cliente = {
    "nome":"John Doe",
    "rg":"12312",
    "cpf":"1234576667",
    "sexo":"feminino"
}
reponse = test.clienteDelete('1/')


print(reponse.status_code)