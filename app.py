import json
import folium
import logging

import pandas as pd
import numpy  as np

from datetime  import datetime
from tkinter   import filedialog
from asyncio   import run
from aiometer  import run_all
from functools import partial
from pathlib import Path

from folium         import Marker, Icon
from folium.plugins import MarkerCluster

from httpx import AsyncClient

# ===========================================================
COORDENADAS_BRASIL = (-15.77972, -47.92972)
BRASIL_API_URL     = 'https://brasilapi.com.br/api/cep/v2/'

# ===========================================================
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
        
    def to_json(self):
        return {
            "cep"           : self.cep,
            "state"         : self.estado,
            "city"          : self.cidade,
            "neighborhood"  : self.bairro,
            "street"        : self.endereco,
            "service"       : self.servico,
            "location"      : {
                "type"       : self.tipo_localizacao,
                "coordinates": {
                    "longitude": self.longitude,
                    "latitude" : self.latitude,
                }
            }
        }

# ===========================================================
def get_dataframe(arquivo):
    # Lendo planilha:
    planilha_df = pd.read_excel(arquivo) # Qualquer planilha .xls que contenha uma coluna "cep"
    
    if 'grupo' not in planilha_df.columns:
        planilha_df['grupo'] = '-'
    if 'latitude' not in planilha_df.columns:
        planilha_df['latitude'] = None
    if 'longitude' not in planilha_df.columns:
        planilha_df['longitude'] = None
    if 'icon' not in planilha_df.columns:
        planilha_df['icon'] = None
    if 'color' not in planilha_df.columns:
        planilha_df['color'] = None
    if 'texto' not in planilha_df.columns:
        planilha_df['texto'] = None
    
    dataframe        = planilha_df[['cep', 'grupo', 'latitude', 'longitude', 'icon', 'color', 'texto']]
    dataframe        = dataframe.dropna(subset=['cep'])
    dataframe['cep'] = dataframe['cep'].apply(lambda x: str(x).replace('.', '').replace('-',''))
    
    return dataframe
    
async def consultar_api(dataframe):
    # Agrupando CEPs iguais
    unique_ceps = list( dataframe['cep'].drop_duplicates().dropna() )    # Brasil API permite CEP com pontos e traços!
    
    # Consumindo API
    tasks    = run_all(
        [partial(buscar_cep, cep) for cep in unique_ceps],
        max_at_once    = 5,
        max_per_second = 2,     #  Por questões de BOM SENSO: Não ultrapasse 2 requisições por segundo!
    )
    results = await tasks
    
    # Salvando o resultado em arquivo .json caso o usuário queira usar posteriormente
    with open(f'brasilapi/{datetime.now():%Y-%m-%d-%H-%M-%S}.json', 'w', encoding='utf8') as file:
        json.dump({r['cep']: r for r in results}, file, ensure_ascii=False)
    
    return results

async def buscar_cep(cep):
    try:
        async with AsyncClient(base_url=BRASIL_API_URL, timeout=10) as client: # TODO: Timeout de ____ segundos
            logging.debug(f'{datetime.now()} chamando {cep}')
            response = await client.get(str(cep))
            logging.debug(f'{datetime.now()} finalizado {cep} com status code {response.status_code}')
        
        if response.status_code == 200:
            return response.json()
    
    except Exception as e:
        logging.error(f'Error ao tentar consumir API para o CEP {cep}', e)
        
    return {}

def atualizar_coordenadas(dataframe:pd.DataFrame, api_results:dict):
    novo_dataframe = dataframe.copy()
    
    for index, row in novo_dataframe.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):    # Não vamos atualizar as linhas que já possuem coordenadas
            continue
        
        try:
            cep         = row['cep']
            coordenadas = api_results.get(cep, {}).get('location', {}).get('coordinates', {})
            
            novo_dataframe.at[index, 'latitude']  = coordenadas.get('latitude', np.nan)     # row['latitude']  = coordenadas.get('latitude' , np.nan)
            novo_dataframe.at[index, 'longitude'] = coordenadas.get('longitude', np.nan)    # row['longitude'] = coordenadas.get('longitude', np.nan)
        except (ValueError, IndexError) as e:
            logging.warning(f'Coordenadas não encontradas para o CEP {cep}', e)
        except Exception as e:
            logging.error(f'Erro ao tentar atualizar coordenadas do CEP {cep}', e)
        
    return novo_dataframe

def gerar_mapa(dataframe:pd.DataFrame):
    mapa = folium.Map(location=COORDENADAS_BRASIL, zoom_start=4, tiles=None, )
    
    # Tipos de Mapa:
    folium.TileLayer('cartodbpositron', attr="CartoDB Positron", name="Preto e Branco").add_to(mapa)
    folium.TileLayer('OpenStreetMap'  , attr="Open Street Map" , name="Satélite").add_to(mapa)
    
    # Marcadores:
    cnt_not_marked = 0
    
    for grupo, group_data in dataframe.groupby('grupo'):
        mark_cluster = MarkerCluster(name=grupo).add_to(mapa)
        for _, row in group_data.iterrows():
            try:
                cep = row["cep"]
                lat = row['latitude']
                lng = row['longitude']
                
                texto = str(row['texto']) if pd.notna(row['texto']) else cep
                icon  = str(row['icon'])  if pd.notna(row['icon'])  else "circle-info"
                color = str(row['color']) if pd.notna(row['color']) else "blue"
                
                if pd.notna(lat) and pd.notna(lng):                    
                    Marker(
                        location = (lat, lng),
                        popup    = texto,
                        # tooltip  = texto,
                        icon     = Icon (
                            prefix = 'fa',
                            icon   = icon,
                            color  = color,
                        ),
                    ).add_to(mark_cluster)
                else:
                    cnt_not_marked += 1
                    logging.warning(f'CEP {cep} não possui localização: ({lat}, {lng})')
            except Exception as e:
                logging.error(f'Erro ao tentar adicionar marcador ao mapa: {cep}', e)
    
    # Quantidade de CEPs que não foram adicionados ao mapa:
    logging.info(f'Um total de {cnt_not_marked} marcadores não foram adicionados ao mapa')
    
    # Controlador:
    folium.LayerControl(collapsed=False).add_to(mapa)
    
    return mapa

def salvar_mapa(mapa):
    filename = f'mapas/{datetime.now():%Y-%m-%d-%H-%M-%S}.html'
    mapa.save(filename)
    logging.info(f'Mapa {filename} salvo com sucesso')

async def main():
    arquivo_excel = filedialog.askopenfilename(title="Arquivo Excel", filetypes=[('.xls', '*.xls')])
    if not arquivo_excel:
        exit()
    
    # Gerando dataframe a partir de um arquivo Excel:
    dataframe = get_dataframe(arquivo_excel)
    
    # Realizando a consulta na API:
    arquivo_json = filedialog.askopenfilename(title="Arquivo JSON", filetypes=[('.json', '*.json')])
        
    if not arquivo_json:
        api_results = await consultar_api(dataframe)
    else:   # Permite que o usuário forneça um arquivo JSON (de consultas anteriores) para não ter que consumir a API novamente.
        # TODO: Permitir que o usuário consulte a API para os CEPs que não estão presentes no JSON
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            api_results = json.load(f)

    # Inserindo colunas de latitude e longitude no dataframe
    novo_dataframe = atualizar_coordenadas(dataframe, api_results)
    
    # Efetivamente gerando o mapa
    mapa = gerar_mapa(novo_dataframe)
        
    # Salvando mapa
    salvar_mapa(mapa)

# ===========================================================
if __name__ == "__main__":
    Path("mapas/").mkdir(parents=True, exist_ok=True)
    Path("brasilapi/").mkdir(parents=True, exist_ok=True)
    Path("logs/").mkdir(parents=True, exist_ok=True)
    
    file_handler   = logging.FileHandler(
        filename = f'logs/{datetime.now():%Y-%m-%d-%H-%M-%S}.log',
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
