from decouple import config

COORDENADAS_BRASIL = (-15.77972, -47.92972)
BRASILAPI_URL = config("BRASILAPI_URL", "https://brasilapi.com.br/api/cep/v2/")
GEOCODE_URL = config("GEOCODE_URL", "https://geocode.xyz/")
MAX_AT_ONCE = config("MAX_AT_ONCE", 10, cast=int)
BRASILAPI_REQUEST_PER_SECOND = config("BRASILAPI_REQUEST_PER_SECOND", 1, cast=int)
