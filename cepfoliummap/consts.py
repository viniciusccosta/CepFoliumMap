from decouple import config

COORDENADAS_BRASIL = (-15.77972, -47.92972)
BRASILAPI_URL = config("BRASILAPI_URL", "https://brasilapi.com.br/api/cep/v2/")
