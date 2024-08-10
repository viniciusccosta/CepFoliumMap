import logging

from httpx import AsyncClient

from cepfoliummap.constants import GEOCODE_URL

logger = logging.getLogger(__name__)


def format_cep(cep):
    """
    Função para formatar um CEP conforme padrão do Geocode.

    Args:
        cep (str): CEP a ser formatado

    Returns:
        str: CEP formatado
    """

    cep_formatado = str(cep)
    cep_formatado = cep_formatado.replace(".", "").replace("-", "")
    cep_formatado = cep_formatado.zfill(8)
    cep_formatado = f"{cep_formatado[0:2]}.{cep_formatado[2:5]}-{cep_formatado[5:8]}"
    logger.debug(f"CEP formatado: {cep_formatado}")

    return cep_formatado


async def consume_geocode_api(cep_formatado, api_key=None):
    try:
        logger.debug(f"Consumindo Geocode | CEP: {cep_formatado}")

        async with AsyncClient(base_url=GEOCODE_URL, timeout=60) as client:
            response = await client.post(
                url="",
                data={
                    "locate": cep_formatado,
                    "auth": api_key,  # TODO: Apenas se diferente de None
                    "geoit": "JSON",
                    "region": "BR",
                },
            )

        return response
    except TimeoutError as e:
        logger.warning(f"TimeoutError | CEP: {cep_formatado}")
        return
    except Exception as e:
        logger.exception(e)
        logger.error(f"Erro ao consultar CEP: {cep_formatado}")
        return


def extract_coordinates_from_json(response_json):
    # Possíveis erros:
    if "error" in response_json:
        logger.warning(f"Geodecode retornou um erro: {response_json}")
        return None, None
    if response_json["latt"] == "Throttled! See geocode.xyz/pricing":
        logger.warning(f"Excedido consultas")
        return None, None

    # Lendo JSON:
    lat = response_json["latt"]
    long = response_json["longt"]

    # Retornando resultado:
    return lat, long


async def get_coordinates_from_cep(cep, api_key=None):
    # Variáveis:
    lat = None
    lng = None

    # Sanitizando e formatando CEP:
    cep_formatado = format_cep(cep)

    # Efetivamente consumindo a API:
    geodecode_response = await consume_geocode_api(cep_formatado, api_key)

    if not geodecode_response:
        return lat, lng

    # Lendo JSON:
    try:
        geodecode_json = geodecode_response.json()
    except Exception as e:
        logger.exception(e)
        logger.error(f"Erro ao tentar ler JSON do GeoCode: {cep}")
        return lat, lng

    # Extraindo coordenadas:
    try:
        lat, lng = extract_coordinates_from_json(geodecode_json)
    except Exception as e:
        logger.exception(e)
        logger.error(f"Erro ao tentar extrair coordenadas do GeoCode: {cep}")
        return lat, lng

    # Retornando resultado:
    return lat, lng
