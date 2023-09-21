# CepFoliumMap

[![MIT License](https://img.shields.io/github/license/viniciusccosta/clipbarcode)](https://choosealicense.com/licenses/mit/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/downloads/release/python-3110/)

O CepFoliumMap é uma ferramenta versátil que permite consultar múltiplos CEPs e criar um mapa interativo em formato HTML com base nesses dados.

## Módulo app.py

O módulo principal deste projeto desempenha um papel central, permitindo que você crie mapas interativos a partir de dados de CEPs. Ele é projetado para ler um arquivo no formato .XLS que deve conter uma coluna com o nome 'cep'. Com base nesses CEPs, o aplicativo gera um mapa interativo utilizando a biblioteca Folium.

### Como Utilizar

Siga estas etapas simples para aproveitar ao máximo o Módulo app.py:

1. Execute o módulo app.py utilizando o seguinte comando:

    ```bash
    python app.py
    ```

2. Escolha o arquivo .xls que contém os CEPs que você deseja visualizar no mapa.
3. Se você já possui um arquivo .json com as coordenadas geográficas correspondentes a cada CEP de execuções anteriores, pode escolher fornecê-lo no processo. Isso pode economizar tempo, evitando consultas adicionais à API da BrasilAPI.
4. Aguarde a geração do mapa.

Após a conclusão do processo, você encontrará os seguintes arquivos na raiz do diretório:

1. **.log**: Este arquivo contém todo o registro da execução, permitindo que você acompanhe o progresso e eventuais erros.
2. **.json**: Caso você tenha optado por realizar consultas à API da BrasilAPI, este arquivo conterá os dados em formato JSON obtidos durante a execução.
3. **.html**: Este é o arquivo principal, que contém o mapa interativo gerado a partir dos CEPs fornecidos. Você pode abri-lo em seu navegador para visualizar o mapa.

## Módulo scrappy.py

O Módulo Scrappy é uma ferramenta especializada que foi desenvolvida para realizar raspagem de informações de sites que oferecem a consulta de CEPs e exibem um mapa do Google Maps incorporado em um iframe. Esse módulo se torna útil quando as consultas à BrasilAPI não retornam as coordenadas geográficas desejadas. O Módulo Scrappy lê um arquivo de texto no qual cada linha representa um CEP (sem pontos ou traços) e extrai as informações necessárias diretamente do site, permitindo uma coleta mais precisa dos dados.

**Nota Importante**: Para utilizar o Módulo Scrappy, é necessário configurar uma variável de ambiente chamada `CEPFOLIUMMAP_SCRAPPY_URL` com a URL do site que permite a consulta de CEPs e exibe um mapa do Google Maps incorporado em um iframe. Esta URL será utilizada pelo Módulo Scrappy para acessar o site e realizar a raspagem de informações.

## Módulo data_merge.py

O Módulo Data Merge foi projetado para combinar os resultados obtidos pelos dois módulos anteriores. Isso significa que você pode criar um mapa interativo usando os dados coletados sem a necessidade de realizar consultas adicionais à BrasilAPI. O Data Merge simplifica o processo de geração de um mapa Folium com os dados consolidados, economizando tempo e recursos.
