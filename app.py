import json
import folium
import logging

import pandas as pd

from datetime  import datetime
from tkinter   import filedialog
from asyncio   import run
from aiometer  import run_all
from functools import partial

from folium import Marker, Icon
from folium.plugins import MarkerCluster

from httpx import AsyncClient

# =======================================
COORDENADAS_BRASIL = (-15.77972, -47.92972)
BRASIL_API_URL     = 'https://brasilapi.com.br/api/cep/v2/'

# =======================================
class Localizacao:
    def __init__(self, brasil_api):
        self.cep         = brasil_api.get('cep')
        self.estado      = brasil_api.get('state')
        self.cidade      = brasil_api.get('city')
        self.bairro      = brasil_api.get('neighborhood')
        self.endereco    = brasil_api.get('street')
        self.servico     = brasil_api.get('service')
        self.localizacao = brasil_api.get('location', {})
        
        self.tipo_localizacao = self.localizacao.get('type', {})
        self.coordenadas      = self.localizacao.get('coordinates', {})
        self.longitude        = self.coordenadas.get('longitude')
        self.latitude         = self.coordenadas.get('latitude')

# =======================================
def get_dataframe(arquivo):
    # Lendo planilha:
    enderecos_df = pd.read_excel(arquivo) # Qualquer planilha .xls que contenha uma coluna "cep"
    ceps_df      = enderecos_df['cep'].dropna()
    ceps_df      = ceps_df.apply(lambda x: str(x).replace('.', '').replace('-',''))
    
    return ceps_df
    
async def consultar_api(ceps_df):
    # Agrupando CEPs iguais
    unique_ceps = list( ceps_df.drop_duplicates().dropna() )    # Brasil API permite CEP com pontos e traços!
    
    # Consumindo API
    tasks    = run_all(
        [partial(buscar_cep, cep) for cep in unique_ceps],
        max_at_once    = 5,
        max_per_second = 2,     #  Por questões de BOM SENSO: Não ultrapasse 2 requisições por segundo!
    )
    results = await tasks
    
    # Salvando o resultado em arquivo .json caso o usuário não queria requisitar tudo novamente
    with open(f'{datetime.now():%Y-%m-%d-%H-%M-%S}.json', 'w', encoding='utf8') as rf:
        json.dump(results, rf)
    
    return results

async def buscar_cep(cep):
    try:
        async with AsyncClient(base_url=BRASIL_API_URL, timeout=10) as client:                          # TODO: Timeout de ____ segundos
            logging.debug(f'{datetime.now()} chamando {cep}')
            response = await client.get(str(cep))
            logging.debug(f'{datetime.now()} finalizado {cep} com status code {response.status_code}')
        
        if response.status_code == 200:
            return response.json()
    
    except Exception as e:
        logging.error(f'Error ao tentar consumir API para o CEP {cep}', e)

def gerar_localizacoes(results):
    localizacoes = [Localizacao(r) for r in results if r]       # Só irá instanciar daqueles que tiveram resposta da API
    return localizacoes

def gerar_mapa(localizacoes, ceps_df):
    mapa = folium.Map(location=COORDENADAS_BRASIL, zoom_start=4, tiles=None, )
    
    # Tipos de Mapa:
    folium.TileLayer('cartodbpositron', attr="CartoDB Positron", name="Preto e Branco").add_to(mapa)
    folium.TileLayer('OpenStreetMap'  , attr="Open Street Map" , name="Satélite").add_to(mapa)
    
    # Marcadores:
    mark_cluster   = MarkerCluster(name="CEPs").add_to(mapa)
    cnt_not_marked = 0
    
    for l in localizacoes:
        qtd = (ceps_df == l.cep).sum()  # Repetindo os marcadores conforme a quantidade de registros desse mesmo CEP
        
        for _ in range(qtd):
            try:
                if l.latitude and l.longitude:
                    Marker(
                        popup    = f'{l.cep}',
                        location = (l.latitude, l.longitude), 
                        icon     = Icon(color='blue', prefix='fa', icon="circle-info"),
                    ).add_to(mark_cluster)
                else:
                    cnt_not_marked += 1
                    logging.warning(f'CEP {l.cep} não possui localização: ({l.latitude}, {l.longitude})')
            except Exception as e:
                logging.error('Erro ao tentar adicionar marcador ao mapa: {l.cep}', e)
    
    # Quantidade de CEPs que não foram adicionados ao mapa:
    logging.info(f'Um total de {cnt_not_marked} marcadores não foram adicionados ao mapa')  # É a quantidade de marcadores e não a quantidade de CEPs (um CEP pode ter mais de 1 marcador)
    
    # Controlador:
    folium.LayerControl().add_to(mapa)
    
    return mapa

def salvar_mapa(mapa):
    filename = f'{datetime.now():%Y-%m-%d-%H-%M-%S}.html'
    mapa.save(filename)
    logging.info(f'Mapa {filename} salvo com sucesso')

async def main():
    arquivo_excel = filedialog.askopenfilename(title="Arquivo Excel", filetypes=[('.xls', '*.xls')])
    if not arquivo_excel:
        exit()
    
    # Gerando dataframe a partir de um arquivo Excel:
    ceps_df = get_dataframe(arquivo_excel)
    
    # Realizando a consulta na API:
    arquivo_json = filedialog.askopenfilename(title="Arquivo JSON", filetypes=[('.json', '*.json')])
    
    if not arquivo_json:
        results = await consultar_api(ceps_df)
    else:   # Permite que o usuário forneça um arquivo JSON (de consultas anteriores) para não ter que consumir a API novamente.
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            results = json.load(f) 

    # Instanciando objetos "Localizacao"
    localizacoes = gerar_localizacoes(results)
    
    # Efetivamente gerando o mapa
    mapa = gerar_mapa(localizacoes, ceps_df)
        
    # Salvando mapa
    salvar_mapa(mapa)

# =======================================
if __name__ == "__main__":
    file_handler   = logging.FileHandler(
        filename = f'{datetime.now():%Y-%m-%d-%H-%M-%S}.log',
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
