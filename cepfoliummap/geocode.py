import logging

from httpx import AsyncClient

from cepfoliummap.constants import GEOCODE_URL


async def scrappy_site(cep, api_key=None):
    """
    Possíveis opções:
        O site "que busca cep" possui dois inputs que contém a latitude e longitude.
            <input type="hidden" id="lat" value="">
            <input type="hidden" id="lng" value="">

    Args:
        cep (str): CEP a ser consultado sem traços ou pontos
        api_key (str): Chave para consumir a API

    Returns:
        dict: Dicionário contendo a latitude e longitude do CEP
    """

    # Variáveis:
    lat = None
    long = None

    # Sanitizando e formatando CEP:
    cep_request = cep
    cep_request = cep_request.replace(".", "").replace("-", "")
    cep_request = cep_request.zfill(8)
    cep_request = f"{cep_request[0:2]}\.{cep_request[2:5]}\-{cep_request[5:8]}"

    # Consultando a página em si:
    try:
        logging.debug(f"{cep}: Acessando site")

        async with AsyncClient(
            base_url=GEOCODE_URL,
            timeout=60,
        ) as client:
            response = await client.post(
                url="",
                data={
                    "locate": cep_request,
                    "auth": api_key,
                    "geoit": "JSON",
                    "region": "BR",
                },
            )

    except TimeoutError as e:
        logging.error(f"TimeoutError | CEP: {cep}")
        return
    except Exception as e:
        logging.exception(e)
        logging.error(f"Erro ao acessar site | CEP: {cep}")
        return

    # Lendo JSON:
    try:
        response_json = response.json()
    except Exception as e:
        logging.exception(e)
        logging.error(f"Erro ao tentar ler JSON | CEP: {cep}")

    # Validando resposta:
    if "error" in response_json:
        # {'longt': '0.00000', ..., 'error': {'description': 'Supply a valid query.', 'code': '007'}, 'latt': '0.00000'}
        logging.warning(f"Retornou um erro | CEP: {cep} | {response_json}")
    elif response_json["latt"] == "Throttled! See geocode.xyz/pricing":
        # {'longt': 'Throttled! See geocode.xyz/pricing', ..., 'latt': 'Throttled! See geocode.xyz/pricing',}
        logging.warning(f"Excedido consultas | CEP: {cep}|")
    else:
        lat = response_json["latt"]
        long = response_json["longt"]

    # Retornando resultado:
    return {
        "cep": cep,
        "latitude": lat,
        "longitude": long,
    }
