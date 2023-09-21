# CepFoliumMap

[![MIT License](https://img.shields.io/github/license/viniciusccosta/clipbarcode)](https://choosealicense.com/licenses/mit/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/downloads/release/python-3110/)

O CepFoliumMap é uma ferramenta versátil que permite consultar múltiplos CEPs e criar um mapa interativo em formato HTML com base nesses dados.

## Módulo app.py

O módulo principal deste projeto é responsável por ler um arquivo no formato .XLS que contenha uma coluna denominada 'cep'. A partir desses CEPs, o aplicativo gera um mapa interativo utilizando a biblioteca Folium. Se você não fornecer um arquivo .JSON que contenha as coordenadas geográficas correspondentes a cada CEP, o sistema realizará consultas à API da BrasilAPI para obter essas informações automaticamente.

## Módulo scrappy.py

O Módulo Scrappy é uma ferramenta especializada que foi desenvolvida para realizar raspagem de informações de sites que oferecem a consulta de CEPs e exibem um mapa do Google Maps incorporado em um iframe. Esse módulo se torna útil quando as consultas à BrasilAPI não retornam as coordenadas geográficas desejadas. O Módulo Scrappy lê um arquivo de texto no qual cada linha representa um CEP (sem pontos ou traços) e extrai as informações necessárias diretamente do site, permitindo uma coleta mais precisa dos dados.

**Nota Importante**: Para utilizar o Módulo Scrappy, é necessário configurar uma variável de ambiente chamada `CEPFOLIUMMAP_SCRAPPY_URL` com a URL do site que permite a consulta de CEPs e exibe um mapa do Google Maps incorporado em um iframe. Esta URL será utilizada pelo Módulo Scrappy para acessar o site e realizar a raspagem de informações.

## Módulo data_merge.py

O Módulo Data Merge foi projetado para combinar os resultados obtidos pelos dois módulos anteriores. Isso significa que você pode criar um mapa interativo usando os dados coletados sem a necessidade de realizar consultas adicionais à BrasilAPI. O Data Merge simplifica o processo de geração de um mapa Folium com os dados consolidados, economizando tempo e recursos.
