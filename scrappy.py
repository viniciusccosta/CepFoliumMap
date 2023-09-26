import re
import bs4
import json
import logging

from datetime     import datetime
from asyncio      import run
from httpx        import AsyncClient
from aiometer     import run_all
from urllib.parse import urlparse
from functools    import partial
from decouple     import config
from tkinter      import messagebox, filedialog
from pathlib      import Path

# ========================================================
URL = config('CEPFOLIUMMAP_SCRAPPY_URL', None)              # Qualquer site que faça consulta por CEP e que possua o mapa do Google embutido na página (dentro de um iframe).

# ========================================================
async def scrappy_site(cep):
    # ------------------------------------------------------
    # Consultando a página em si:
    logging.debug(f"{cep}: Acessando site")
    try:
        async with AsyncClient(base_url=URL) as client:
            response = await client.get(f'{cep}/')
    except Exception as e:
        logging.error(f"{cep}:\tErro ao acessar site", e)
        return
    
    # ------------------------------------------------------
    # Consultando cada iFrame da página (supostamente só tem 1 nessa página):
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    
    iframes = soup.select('iframe')
    if len(iframes) != 1:                    # TODO: Realizar alterações para permitir que tenha mais de 1 iFrame
        logging.error(f'{cep}:\tQuantidade de iFrames é diferente de 1')
        return

    # ------------------------------------------------------
    # Consultando iFrame:
    logging.debug(f"{cep}: Gerando iFrame")
    iframe = iframes[0]
    try:
        async with AsyncClient() as client:
            url = urlparse( iframe.attrs['src'] ).geturl()
            iframe_response = await client.get(url)
    except Exception as e:
        logging.error(f"{cep}:\tErro ao consultar iframe", e)
        return
    
    # ------------------------------------------------------
    # Recuperando latitude e longitude do mapa:
    logging.debug(f"{cep}: Recuperando latitude e longitude")
    
    pattern = r'\[-?\d{1,2}.\d{4,}\, *-?\d{1,2}\.\d{4,}\]'  # Acredito que é necessário pelo menos 4 casas depois da vírgula para ter o mínimo de precisão
    matches = re.findall(pattern, iframe_response.text)
    
    if len(matches) < 1:
        logging.error(f'{cep}:\tLatitude e longitude não foram encontradas')
        return
    
    # ------------------------------------------------------
    lat, long = eval(matches[0])
    logging.info(f"{cep}: Latitude e Longitude encontrados com sucesso")
    return {'latitude': lat, 'longitude': long}

async def main():
    # Arquivo:
    ceps_file = filedialog.askopenfilename(title='Arquivo com CEPs', filetypes=[('txt', '*.txt')])
    if not ceps_file:
        messagebox.showerror(title="Erro", message="Necessário informar um arquivo que contenha 1 CEP por linha")
        return
    
    # Populando lista de CEPs:
    ceps = set()
    with open(ceps_file, 'r', encoding='utf-8') as f:
        for l in f.readlines():
            cep = l.replace('-','').replace('\n','')        # TODO: Validar: 1) Só pode ter 1 CEP por linha, 2) Ter 8 dígitos, ...
            ceps.add(cep)
    
    # Procurando pelos CEPs:
    tasks = run_all(
        [partial(scrappy_site, cep) for cep in ceps],
        max_at_once   =5,
        max_per_second=2,
    )
    results = await tasks
    
    # Guardando resultado:
    with open(f'scrapps/scrappy-{datetime.now():%Y-%m-%d-%H-%M-%S}.json', 'w', encoding='utf-8') as f:
        result_dict = {key: value for key, value in zip(ceps, results)}
        json.dump(result_dict, f, ensure_ascii=False)

# ========================================================
if __name__ == "__main__":
    Path("scrapps/").mkdir(parents=True, exist_ok=True)
    Path("logs/").mkdir(parents=True, exist_ok=True)
    
    if not URL:
        messagebox.showerror(title="Erro", message="Necessário configurar a variável de ambiente CEPFOLIUMMAP_SCRAPPY_URL")
        exit(0)
    
    file_handler   = logging.FileHandler(
        filename = f'logs/scrappy-{datetime.now():%Y-%m-%d-%H-%M-%S}.log',
        mode     = 'w',
        encoding = 'utf-8',   
    )
    stream_handler = logging.StreamHandler()
    
    logging.basicConfig (
        level    = logging.DEBUG,
        encoding = 'utf-8',
        format   = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers = [
            file_handler,
            stream_handler
        ]
    )
    
    run( main() )
