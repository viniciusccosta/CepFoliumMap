import logging

import bs4
from httpx import AsyncClient


async def scrappy_site(cep, url):
    """
    Possíveis opções:
        O site "que busca cep" possui dois inputs que contém a latitude e longitude.
            <input type="hidden" id="lat" value="">
            <input type="hidden" id="lng" value="">

    Args:
        cep (str): CEP a ser consultado sem traços ou pontos
        url (str): URL do site a ser consultado faltando apenas o CEP

    Returns:
        dict: Dicionário contendo a latitude e longitude do CEP
    """

    # Consultando a página em si:
    try:
        logging.debug(f"{cep}: Acessando site")
        async with AsyncClient(base_url=url) as client:
            response = await client.get(f"{cep}/")
    except TimeoutError as e:
        logging.error(f"TimeoutError | CEP: {cep}")
        return
    except Exception as e:
        logging.exception(e)
        logging.error(f"Erro ao acessar site | CEP: {cep}")
        return

    # Parseando a página:
    soup = bs4.BeautifulSoup(response.text, "html.parser")

    # Recuperando as coordenadas:
    lat = soup.select_one("#lat").get("value")
    long = soup.select_one("#lng").get("value")

    # Retornando resultado:
    return {"cep": cep, "latitude": lat, "longitude": long}
