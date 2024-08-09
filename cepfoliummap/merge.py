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


def merge_results(app_file, geodecode_file):
    def gerar_localizacoes(results):
        localizacoes = [Localizacao(r) for cep, r in results.items() if cep]
        return localizacoes

    # Criando diretórios:
    Path("logs/").mkdir(parents=True, exist_ok=True)
    Path("merges/").mkdir(parents=True, exist_ok=True)

    # Carregando resultados:
    app_results = json.load(open(app_file, "r", encoding="utf8"))
    geodecode_results = json.load(open(geodecode_file, "r", encoding="utf8"))

    # Gerando objetos "Localização"
    localizacoes = gerar_localizacoes(app_results)

    # Atualizando coordenadas das localizações que não possuem latitude e longitude:
    for l in localizacoes:
        if not (l.latitude and l.longitude):
            # Existe esse CEP no resultado do geodecode e possui valores:
            if geodecode_results.get(l.cep):
                # Caso "geodecode_results[cep]" não possua latitude, simplesmente não fará diferença
                l.latitude = geodecode_results[l.cep].get("latitude")

                # Caso "geodecode_results[cep]" não possua longitude, simplesmente não fará diferença
                l.longitude = geodecode_results[l.cep].get("longitude")

    # Salva resultado:
    result = {l.cep: l.to_json() for l in localizacoes}
    return result
