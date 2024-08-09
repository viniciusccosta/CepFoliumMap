# CepFoliumMap

[![MIT License](https://img.shields.io/github/license/viniciusccosta/clipbarcode)](https://choosealicense.com/licenses/mit/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/downloads/release/python-3110/)

O CepFoliumMap é uma ferramenta versátil que permite consultar múltiplos CEPs e criar um mapa interativo em formato HTML com base nesses dados.

## Como Usar

### Primeira Aba: "Folium Map"

Nesta aba, você pode gerar mapas interativos no formato `.html` a partir de um arquivo `.xls` fornecido.

- Arquivo `.xls`: O arquivo deve conter as colunas: [cep, grupo, latitude, longitude, icon, color, texto], sendo apenas a coluna `cep` obrigatória.
- Arquivo JSON (Opcional): Você pode fornecer um arquivo JSON com as informações de coordenadas para os CEPs. Caso não forneça este arquivo, o programa irá gerar um novo, consultando a BrasilAPI para obter as coordenadas. Este processo pode demorar alguns minutos, dependendo da quantidade de CEPs.

### Segunda Aba: "Geodecode"

Nesta aba, você pode tentar recuperar a latitude e longitude de CEPs que não foram encontrados pela BrasilAPI.

- Arquivo `.xls`: Forneça um arquivo com a coluna `cep`.
- Chave de API: Caso possua uma chave do Geodecode para realizar mais de 1 requisição por segundo.

### Terceira Aba: "Data Merger"

Use esta aba quando precisar combinar os resultados obtidos nas abas anteriores.

- Arquivo JSON (BrasilAPI): Forneça o arquivo JSON gerado a partir da primeira aba.
- Arquivo JSON (Geodecode): Forneça o arquivo JSON gerado a partir da segunda aba.

O programa combinará as informações, gerando um novo arquivo JSON consolidado que pode ser usado na primeira aba para evitar consultas desnecessárias à BrasilAPI.

## Contribuições

Este é um projeto open source e recebe contribuições da comunidade. Caso você queira contribuir, siga os passos abaixo:

- Faça um fork do repositório.
- Implemente as alterações desejadas ou corrija bugs.
- Faça um pull request para enviar suas alterações.
- Aguarde a análise e a revisão da sua contribuição pela equipe responsável.

## Licença

O CepFoliumMap é distribuído sob a licença MIT. Para mais detalhes, consulte o arquivo LICENSE.
