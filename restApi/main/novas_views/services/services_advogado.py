from django.conf import settings

class AdvogadoService:
    def __init__(self, repository: object) -> None:
        self.chave_esperada = str(getattr(settings,'API_SECRET_KEY'))

    def validate_chave_login(self,chave: str)-> bool:
        if chave == self.chave_esperada:
            return True
        else:
            return False