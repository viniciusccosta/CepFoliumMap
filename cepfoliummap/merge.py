import json
from datetime import datetime
from pathlib import Path


class Localizacao:
    def __init__(self, brasil_api):
        self.cep = brasil_api.get("cep")
        self.estado = brasil_api.get("state")
        self.cidade = brasil_api.get("city")
        self.bairro = brasil_api.get("neighborhood")
        self.endereco = brasil_api.get("street")
        self.servico = brasil_api.get("service")
        self.localizacao = brasil_api.get("location", {})

        self.tipo_localizacao = self.localizacao.get("type", {})
        self.coordenadas = self.localizacao.get("coordinates", {})
        self.longitude = self.coordenadas.get("longitude")
        self.latitude = self.coordenadas.get("latitude")

    def to_json(self):
        return {
            "cep": self.cep,
            "state": self.estado,
            "city": self.cidade,
            "neighborhood": self.bairro,
            "street": self.endereco,
            "service": self.servico,
            "location": {
                "type": self.tipo_localizacao,
                "coordinates": {
                    "longitude": self.longitude,
                    "latitude": self.latitude,
                },
            },
        }


def merge_results(app_file, scrappy_file):
    def gerar_localizacoes(results):
        localizacoes = [Localizacao(r) for cep, r in results.items() if cep]
        return localizacoes

    # Criando diretórios:
    Path("logs/").mkdir(parents=True, exist_ok=True)
    Path("merges/").mkdir(parents=True, exist_ok=True)

    # Carregando resultados:
    app_results = json.load(open(app_file, "r", encoding="utf8"))
    scrappy_results = json.load(open(scrappy_file, "r", encoding="utf8"))

    # Gerando objetos "Localização"
    localizacoes = gerar_localizacoes(app_results)

    # Atualizando coordenadas das localizações que não possuem latitude e longitude:
    for l in localizacoes:
        if not (l.latitude and l.longitude):
            # Existe esse CEP no resultado do scrappy e possui valores:
            if scrappy_results.get(l.cep):
                # Caso "scrappy_result[cep]" não possua latitude, simplesmente não fará diferença
                l.latitude = scrappy_results[l.cep].get("latitude")

                # Caso "scrappy_result[cep]" não possua longitude, simplesmente não fará diferença
                l.longitude = scrappy_results[l.cep].get("longitude")

    # Salva resultado:
    result = {l.cep: l.to_json() for l in localizacoes}
    return result
