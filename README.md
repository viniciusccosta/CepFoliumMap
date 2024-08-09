# CepFoliumMap

[![MIT License](https://img.shields.io/github/license/viniciusccosta/clipbarcode)](https://choosealicense.com/licenses/mit/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/downloads/release/python-3110/)

O CepFoliumMap é uma ferramenta versátil que permite consultar múltiplos CEPs e criar um mapa interativo em formato HTML com base nesses dados.

## Pré-Requisitos

Para começar com o projeto, certifique-se de seguir estas etapas iniciais:

### Clone do Repositório

Certifique-se de ter uma cópia local do repositório. Você pode fazer isso clonando o repositório usando o comando:

```bash
git clone https://github.com/viniciusccosta/CepFoliumMap
```

### Criação de um Ambiente Virtual (Recomendado, mas Opcional)

Embora seja opcional, é altamente recomendado criar um ambiente virtual para isolar as dependências do projeto. Isso ajuda a evitar conflitos com outras bibliotecas Python que você pode ter instalado em seu sistema. Você pode criar um ambiente virtual usando ferramentas como venv ou virtualenv.

### Instalação das dependências

Use o seguinte comando para instalar todas as dependências necessárias para o projeto:

```bash
poetry install
```

Certifique-se de que você tenha o Poetry instalado em seu ambiente Python. Isso garantirá que todas as bibliotecas necessárias sejam baixadas e configuradas corretamente para o projeto.

## Módulos

### App.py

O módulo principal deste projeto desempenha um papel central, permitindo que você crie mapas interativos a partir de dados de CEPs. Ele é projetado para ler um arquivo no formato .XLS que deve conter uma coluna com o nome 'cep'. Com base nesses CEPs, o aplicativo gera um mapa interativo utilizando a biblioteca Folium.

#### Como Utilizar

Siga estas etapas simples para aproveitar ao máximo o Módulo app.py:

1. Execute o módulo app.py utilizando o seguinte comando:

    ```bash
    python app.py
    ```

2. Escolha o arquivo .xls que contém os CEPs que você deseja visualizar no mapa.
3. Se você já possui um arquivo .json com as coordenadas geográficas correspondentes a cada CEP de execuções anteriores, pode escolher fornecê-lo no processo. Isso pode economizar tempo, evitando consultas adicionais à API da BrasilAPI.
4. Aguarde a geração do mapa.

Após a conclusão do processo, você encontrará os seguintes arquivos na raiz do diretório:

1. **{datetime}.log**: Este arquivo contém todo o registro da execução, permitindo que você acompanhe o progresso e eventuais erros.
2. **{datetime}.json**: Caso você tenha optado por realizar consultas à API da BrasilAPI, este arquivo conterá os dados em formato JSON obtidos durante a execução.
3. **{datetime}.html**: Este é o arquivo principal, que contém o mapa interativo gerado a partir dos CEPs fornecidos. Você pode abri-lo em seu navegador para visualizar o mapa.

### Scrappy.py

O Módulo Scrappy é uma ferramenta especializada que foi desenvolvida para realizar raspagem de informações de sites que oferecem a consulta de CEPs e exibem um mapa do Google Maps incorporado em um iframe. Esse módulo se torna útil quando as consultas à BrasilAPI não retornam as coordenadas geográficas desejadas. O Módulo Scrappy lê um arquivo de texto no qual cada linha representa um CEP (sem pontos ou traços) e extrai as informações necessárias diretamente do site, permitindo uma coleta mais precisa dos dados.

#### Como usar

Siga estas etapas simples para aproveitar ao máximo o Módulo app.py:

1. Antes de executar o Módulo Scrappy, certifique-se de ter criado a variável de ambiente `SCRAPPY_URL`. Isso pode ser feito por meio de um arquivo .env ou diretamente no terminal, configurando a URL do site que permite a consulta de CEPs e exibe o mapa do Google Maps incorporado no iframe.
2. Execute o módulo 'scrappy.py' usando o seguinte comando:

    ```bash
    python scrappy.py
    ```

3. Escolha o arquivo .txt que contém os CEPs (sem pontos ou traços) que você deseja processar e para os quais deseja obter informações de localização.
4. Aguarde a conclusão do processo de scrapping. Em nossa experiência de teste, um arquivo contendo 180 CEPs levou aproximadamente 90 segundos para ser processado, mas o tempo pode variar dependendo do número de CEPs e da velocidade da sua conexão.

Após a conclusão do processo, você encontrará os seguintes arquivos na raiz do diretório:

1. **scrapy-{datetime}.log**: Este arquivo contém todo o registro da execução, permitindo que você acompanhe o progresso e eventuais erros.
2. **scrapy-{datetime}.json**: Este arquivo contém o resultado da operação de scrapping, com as informações de localização obtidas a partir dos CEPs processados.

### Data_merge.py

O Módulo Data Merge foi projetado para reunir e consolidar os resultados obtidos pelos dois módulos anteriores. Isso significa que você pode criar um mapa interativo utilizando os dados coletados, eliminando a necessidade de realizar consultas adicionais à BrasilAPI. O Data Merge simplifica significativamente o processo de geração de um mapa Folium com informações unificadas, poupando tempo e recursos.

#### Como Usar

Siga estas simples etapas para aproveitar ao máximo o Módulo Data Merge:

1. Execute o módulo 'data_merger.py' usando o seguinte comando:

    ```bash
    python data_merger.py
    ```

2. Selecione o arquivo JSON resultante da execução do Módulo "app.py". Esse arquivo conterá os dados geográficos obtidos a partir do arquivo .XLS que você forneceu como entrada.
3. Selecione o arquivo JSON resultante da execução do Módulo "scrappy.py". Este arquivo deve conter as informações geográficas obtidas por meio de raspagem de sites.
4. Aguarde a conclusão do processo.

Após a conclusão do processo, você encontrará os seguintes arquivos na raiz do diretório:

1. **merge-{datetime}.json**: Este arquivo contém os dados consolidados, prontos para serem utilizados na geração de um novo mapa interativo.

Para criar um novo mapa interativo com os dados consolidados, você pode executar novamente o Módulo "app.py". Ao fazer isso, selecione o arquivo "merge-.json" como entrada. Isso permitirá que você crie um mapa com todos os dados reunidos a partir das execuções anteriores, sem a necessidade de repetir o processo de coleta de informações. Dessa forma, você economiza tempo e recursos, simplificando a visualização de dados geográficos.

## Contribuições

Este é um projeto open source e recebe contribuições da comunidade. Caso você queira contribuir, siga os passos abaixo:

- Faça um fork do repositório.
- Implemente as alterações desejadas ou corrija bugs.
- Faça um pull request para enviar suas alterações.
- Aguarde a análise e a revisão da sua contribuição pela equipe responsável.

## Licença

O CepFoliumMap é distribuído sob a licença MIT. Para mais detalhes, consulte o arquivo LICENSE.
