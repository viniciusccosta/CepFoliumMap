import logging

from httpx import AsyncClient

from cepfoliummap.constants import GEOCODE_URL


async def get_coordinates(cep, api_key=None):
    """
    Função para consultar a latitude e longitude de um CEP.

    Args:
        cep (str): CEP a ser consultado sem traços ou pontos
        api_key (str): Chave para consumir a API com limite diferenciado.

    Returns:
        dict: Dicionário contendo a latitude e longitude do CEP
    """

    # Variáveis:
    lat = None
    long = None

    # Sanitizando e formatando CEP:
    cep_formatado = cep
    cep_formatado = cep_formatado.replace(".", "").replace("-", "")
    cep_formatado = cep_formatado.zfill(8)
    cep_formatado = f"{cep_formatado[0:2]}.{cep_formatado[2:5]}-{cep_formatado[5:8]}"
    logging.debug(f"CEP formatado: {cep_formatado}")

    # Efetivamente consumindo a API:
    try:
        logging.debug(f"Consultando CEP: {cep}")

        async with AsyncClient(base_url=GEOCODE_URL, timeout=60) as client:
            response = await client.post(
                url="",
                data={
                    "locate": cep_formatado,
                    "auth": api_key,
                    "geoit": "JSON",
                    "region": "BR",
                },
            )
    except TimeoutError as e:
        logging.warning(f"TimeoutError | CEP: {cep}")
        return
    except Exception as e:
        logging.exception(e)
        logging.error(f"Erro ao consultar CEP: {cep}")
        return

    # Lendo JSON:
    try:
        logging.debug(f"Lendo JSON | CEP: {cep}")
        response_json = response.json()
    except Exception as e:
        logging.exception(e)
        logging.error(f"Erro ao tentar ler JSON | CEP: {cep}")
        return

    # Validando resposta:
    if "error" in response_json:
        logging.warning(f"Retornou um erro | CEP: {cep} | {response_json}")
    elif response_json["latt"] == "Throttled! See geocode.xyz/pricing":
        logging.warning(f"Excedido consultas | CEP: {cep}|")
    else:
        logging.debug(f"CEP consultado com sucesso | CEP: {cep}")
        lat = response_json["latt"]
        long = response_json["longt"]
        logging.debug(f"CEP: {cep}| Latitude: {lat} | Longitude: {long}")

    # Retornando resultado:
    return {
        "cep": cep,
        "latitude": lat,
        "longitude": long,
    }
