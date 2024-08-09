import asyncio
import json
import logging
import tkinter as tk
from datetime import datetime
from functools import partial
from tkinter import filedialog, messagebox

import folium
import numpy as np
import pandas as pd
import ttkbootstrap as ttk
from aiometer import run_all
from folium import Icon, Marker
from folium.plugins import MarkerCluster
from httpx import AsyncClient
from ttkbootstrap.tooltip import ToolTip

from cepfoliummap.consts import BRASILAPI_URL, COORDENADAS_BRASIL
from cepfoliummap.merge import merge_results
from cepfoliummap.scrappy import scrappy_site


class CepFoliumMapFrame(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master

        # Arquivo Excel:
        lf_excel = ttk.Labelframe(
            self,
            text="Arquivo Excel (cep, grupo, latitude, longitude, icon, color, texto)",
        )
        lf_excel.pack(pady=5, padx=5, fill="x", expand=False)

        self.arquivo_excel = tk.StringVar()
        ttk.Entry(lf_excel, textvariable=self.arquivo_excel).grid(
            row=0, column=0, sticky="ew", padx=5, pady=5
        )
        ttk.Button(lf_excel, text="Buscar", command=self.buscar_xls).grid(
            row=0, column=1, padx=5, pady=5
        )

        lf_excel.columnconfigure(0, weight=1)

        # Arquivo JSON (permite que o usuário forneça um arquivo JSON (de consultas anteriores) para não ter que consumir a API novamente):
        lf_json = ttk.Labelframe(
            self,
            text="Arquivo JSON [opcional]",
        )
        lf_json.pack(pady=5, padx=5, fill="x", expand=False)

        ToolTip(
            lf_json,
            text="Caso você tenha consultado a API anteriormente e deseja reutilizar os resultados, selecione o arquivo JSON aqui.",
        )

        self.arquivo_json = tk.StringVar()
        ttk.Entry(lf_json, textvariable=self.arquivo_json).grid(
            row=0, column=0, sticky="ew", padx=5, pady=5
        )
        ttk.Button(lf_json, text="Buscar", command=self.buscar_json).grid(
            row=0, column=1, padx=5, pady=5
        )

        lf_json.columnconfigure(0, weight=1)

        # Botão de execução:
        # TODO: Thread para não travar a interface
        ttk.Button(
            self,
            text="Executar",
            command=lambda: asyncio.run(self.executar()),
        ).pack(pady=5, padx=5)

    def buscar_xls(self):
        arquivo_excel = filedialog.askopenfilename(
            title="Arquivo Excel",
            filetypes=[(".xls", "*.xls")],
        )
        if arquivo_excel:
            self.arquivo_excel.set(arquivo_excel)
            logging.info(f"Arquivo Excel selecionado: {arquivo_excel}")

        # Liberar botão de execução se arquivo arquivo_excel.get() não é None|Vazio

    def buscar_json(self):
        arquivo_json = filedialog.askopenfilename(
            title="Arquivo JSON",
            filetypes=[(".json", "*.json")],
        )
        if arquivo_json:
            self.arquivo_json.set(arquivo_json)
            logging.info(f"Arquivo JSON selecionado: {arquivo_json}")

    async def executar(self):
        # TODO: Renomear a função para algo mais descritivo

        # TODO: Refatorar as validações para uma função própria
        # Verificando se o arquivo Excel foi selecionado:
        arquivo_excel = self.arquivo_excel.get()
        if not arquivo_excel:
            messagebox.showerror("Erro", "Nenhum arquivo Excel foi selecionado")
            logging.info("Nenhum arquivo Excel foi selecionado")
            return

        # Gerando dataframe a partir de um arquivo Excel:
        dataframe = self.get_dataframe(arquivo_excel)

        # Realizando a consulta na API (se necessário):
        arquivo_json = self.arquivo_json.get()

        # TODO: Validar arquivo json
        # TODO: Permitir que o usuário consulte a API para os CEPs que não estão presentes no JSON
        if arquivo_json:
            with open(arquivo_json, "r", encoding="utf-8") as f:
                api_results = json.load(f)
        else:
            api_results = await self.consultar_api(dataframe)

        # Inserindo colunas de latitude e longitude no dataframe:
        df_coordenadas = self.incluir_coordenadas(dataframe, api_results)

        # Efetivamente gerando o mapa
        mapa = self.gerar_mapa(df_coordenadas)

        # Salvando mapa
        self.salvar_mapa(mapa)

        # Feedback para o usuário:
        logging.info("Mapa gerado com sucesso")
        messagebox.showinfo("Sucesso", "Mapa gerado com sucesso")

    def get_dataframe(self, filename):
        """
        Função que lê um arquivo Excel e retorna um DataFrame com as colunas "cep", "grupo", "latitude", "longitude", "icon", "color" e "texto".

        Args:
            arquivo(str): Caminho do arquivo Excel

        Returns:
            pd.DataFrame
        """
        # Lendo planilha (xls que contenha uma coluna "cep"):
        planilha_df = pd.read_excel(filename)

        # Verificando se as colunas necessárias existem:
        if "grupo" not in planilha_df.columns:
            planilha_df["grupo"] = "-"
        if "latitude" not in planilha_df.columns:
            planilha_df["latitude"] = None
        if "longitude" not in planilha_df.columns:
            planilha_df["longitude"] = None
        if "icon" not in planilha_df.columns:
            planilha_df["icon"] = None
        if "color" not in planilha_df.columns:
            planilha_df["color"] = None
        if "texto" not in planilha_df.columns:
            planilha_df["texto"] = None

        dataframe = planilha_df[
            ["cep", "grupo", "latitude", "longitude", "icon", "color", "texto"]
        ]

        # Removendo linhas que não possuem CEP:
        dataframe = dataframe.dropna(subset=["cep"])

        # Removendo pontos e traços do CEP:
        dataframe["cep"] = dataframe["cep"].apply(
            lambda x: str(x).replace(".", "").replace("-", "")
        )

        return dataframe

    async def consultar_api(self, dataframe):
        """
        Função que consome a API do BrasilAPI para obter as coordenadas dos CEPs, com várias requisições assíncronas.

        Args:
            dataframe (pd.DataFrame): DataFrame com todas as colunas necessárias

        Returns:
            json: Dicionário com os resultados da API
        """
        # Resultado:
        result = {}

        # Agrupando CEPs iguais
        unique_ceps = list(dataframe["cep"].drop_duplicates().dropna())

        # Consumindo API
        tasks = run_all(
            [partial(self.buscar_cep, cep) for cep in unique_ceps],
            max_at_once=5,
            max_per_second=2,  #  Por questões de BOM SENSO: Não ultrapasse 2 requisições por segundo!
        )
        api_results = await tasks

        # Salvando o resultado em arquivo .json caso o usuário queira usar posteriormente
        with open(
            file=f"brasilapi/{datetime.now():%Y-%m-%d-%H-%M-%S}.json",
            mode="w",
            encoding="utf8",
        ) as file:
            for api_result in api_results:
                try:
                    cep = api_result.get("cep")
                    result[cep] = api_result
                except Exception as e:
                    logging.error(f"Erro ao tentar salvar resultado do CEP {cep}", e)
                    logging.exception(e)

            json.dump(result, file, ensure_ascii=False)

        # Retornando resultado:
        return result

    async def buscar_cep(self, cep):
        """
        Função que efetivamente consome a API do BrasilAPI para obter as coordenadas de um CEP de forma assíncrona.
        """

        try:
            # TODO: Timeout de ____ segundos
            async with AsyncClient(base_url=BRASILAPI_URL, timeout=10) as client:
                logging.debug(f"{datetime.now()} chamando {cep}")
                response = await client.get(str(cep))
                logging.debug(
                    f"{datetime.now()} finalizado {cep} com status code {response.status_code}"
                )

            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logging.exception(e)
            logging.error(f"Error ao tentar consumir API para o CEP {cep}", e)

        return {}

    def incluir_coordenadas(self, dataframe: pd.DataFrame, api_results: dict):
        df_coordenadas = dataframe.copy()

        for index, row in df_coordenadas.iterrows():
            if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
                # Não vamos atualizar as linhas que já possuem coordenadas
                continue

            try:
                cep = row["cep"]
                coordenadas = (
                    api_results.get(cep, {}).get("location", {}).get("coordinates", {})
                )

                df_coordenadas.at[index, "latitude"] = coordenadas.get(
                    "latitude", np.nan
                )
                df_coordenadas.at[index, "longitude"] = coordenadas.get(
                    "longitude", np.nan
                )
            except (ValueError, IndexError) as e:
                logging.warning(f"Coordenadas não encontradas para o CEP {cep}", e)
            except Exception as e:
                logging.exception(e)
                logging.error(f"Erro ao tentar atualizar coordenadas do CEP {cep}", e)

        return df_coordenadas

    def gerar_mapa(self, dataframe: pd.DataFrame):
        mapa = folium.Map(
            location=COORDENADAS_BRASIL,
            zoom_start=4,
            tiles=None,
        )

        # Tipos de Mapa:
        folium.TileLayer(
            "cartodbpositron", attr="CartoDB Positron", name="Preto e Branco"
        ).add_to(mapa)
        folium.TileLayer(
            "OpenStreetMap", attr="Open Street Map", name="Satélite"
        ).add_to(mapa)

        # Marcadores:
        cnt_not_marked = 0

        for grupo, group_data in dataframe.groupby("grupo"):
            mark_cluster = MarkerCluster(name=grupo).add_to(mapa)
            for _, row in group_data.iterrows():
                try:
                    cep = row["cep"]
                    lat = row["latitude"]
                    lng = row["longitude"]

                    texto = str(row["texto"]) if pd.notna(row["texto"]) else cep
                    icon = str(row["icon"]) if pd.notna(row["icon"]) else "circle-info"
                    color = str(row["color"]) if pd.notna(row["color"]) else "blue"

                    if pd.notna(lat) and pd.notna(lng):
                        Marker(
                            location=(lat, lng),
                            popup=texto,
                            # tooltip  = texto,
                            icon=Icon(
                                prefix="fa",
                                icon=icon,
                                color=color,
                            ),
                        ).add_to(mark_cluster)
                    else:
                        cnt_not_marked += 1
                        logging.warning(
                            f"CEP {cep} não possui localização: ({lat}, {lng})"
                        )
                except Exception as e:
                    logging.exception(e)
                    logging.error(f"Erro ao tentar adicionar marcador ao mapa: {cep}")

        # Quantidade de CEPs que não foram adicionados ao mapa:
        logging.info(
            f"Um total de {cnt_not_marked} marcadores não foram adicionados ao mapa"
        )

        # Controlador:
        folium.LayerControl(collapsed=False).add_to(mapa)

        return mapa

    def salvar_mapa(self, mapa):
        # TODO: Permitir que o usuário escolha o local de salvamento

        filename = f"mapas/{datetime.now():%Y-%m-%d-%H-%M-%S}.html"
        mapa.save(filename)


class ScrappyFrame(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master

        # Arquivo Excel:
        lf_excel = ttk.Labelframe(self, text="Arquivo Excel")
        lf_excel.pack(pady=5, padx=5, fill="x", expand=False)

        self.arquivo_excel = tk.StringVar()
        ttk.Entry(lf_excel, textvariable=self.arquivo_excel).grid(
            row=0, column=0, sticky="ew", padx=5, pady=5
        )
        ttk.Button(lf_excel, text="Buscar", command=self.buscar_xls).grid(
            row=0, column=1, padx=5, pady=5
        )

        lf_excel.columnconfigure(0, weight=1)

        # URL
        lf_url = ttk.Labelframe(self, text="URL")
        lf_url.pack(pady=5, padx=5, fill="x", expand=False)

        self.url = tk.StringVar()
        ttk.Entry(lf_url, textvariable=self.url).grid(
            row=0, column=0, sticky="ew", padx=5, pady=5
        )

        lf_url.columnconfigure(0, weight=1)

        # Botão de execução:
        # TODO: Thread para não travar a interface
        ttk.Button(
            self,
            text="Executar",
            command=lambda: asyncio.run(self.executar()),
        ).pack(pady=5, padx=5)

    def buscar_xls(self):
        arquivo_excel = filedialog.askopenfilename(
            title="Arquivo Excel",
            filetypes=[(".xls", "*.xls")],
        )
        if arquivo_excel:
            self.arquivo_excel.set(arquivo_excel)
            logging.info(f"Arquivo Excel selecionado: {arquivo_excel}")

        # TODO: Liberar botão de execução se arquivo arquivo_excel.get() não é None|Vazio

    async def executar(self):
        # TODO: Renomear a função para algo mais descritivo

        # Verificando se o arquivo Excel foi selecionado:
        # TODO: Refatorar essas validações para uma função própria:
        arquivo_excel = self.arquivo_excel.get()
        if not arquivo_excel:
            messagebox.showerror("Erro", "Nenhum arquivo Excel foi selecionado")
            logging.info("Nenhum arquivo Excel foi selecionado")
            return

        # Verificando se a URL foi preenchida:
        # TODO: Refatorar essas validações para uma função própria:
        url = self.url.get()
        if not url:
            messagebox.showerror("Erro", "Nenhuma URL foi informada")
            logging.info("Nenhuma URL foi informada")
            return

        # Populando lista de CEPs:
        try:
            dataframe = self.get_dataframe(arquivo_excel)
            ceps = dataframe["cep"].tolist()
        except Exception as e:
            logging.exception(e)
            logging.error("Erro ao tentar ler o arquivo Excel")
            return

        # Procurando pelos CEPs:
        try:
            # TODO: Refatorar para uma função própria
            tasks = run_all(
                [partial(scrappy_site, cep, url) for cep in ceps],
                max_at_once=5,
                max_per_second=2,
            )
            results = await tasks
        except Exception as e:
            logging.exception(e)
            logging.error("Erro ao tentar buscar os CEPs")
            return

        # Guardando resultado:
        try:
            results = {cep: r for cep, r in zip(ceps, results)}
            self.salvar_scrappy(results)
        except Exception as e:
            logging.exception(e)
            logging.error("Erro ao tentar salvar o resultado")
            return

        # Feedback para o usuário:
        logging.info("Scrappy realizado com sucesso")
        messagebox.showinfo("Sucesso", "Scrappy realizado com sucesso")

    def get_dataframe(self, filename):
        """
        Função que lê um arquivo Excel e retorna um DataFrame.

        Args:
            arquivo(str): Caminho do arquivo Excel

        Returns:
            pd.DataFrame
        """

        # Lendo planilha (xls que contenha uma coluna "cep"):
        planilha_df = pd.read_excel(filename)
        planilha_df = planilha_df.drop_duplicates().dropna(subset=["cep"])
        planilha_df["cep"] = planilha_df["cep"].apply(
            lambda x: str(x).replace(".", "").replace("-", "")
        )

        return planilha_df

    def salvar_scrappy(self, scrappy_results):
        # TODO: Permitir que o usuário escolha o local de salvamento

        with open(
            file=f"scrapps/scrappy-{datetime.now():%Y-%m-%d-%H-%M-%S}.json",
            mode="w",
            encoding="utf-8",
        ) as f:
            json.dump(scrappy_results, f, ensure_ascii=False)


class MergeFrame(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master

        # Arquivo BrasilAPI:
        lf_brasilapi = ttk.Labelframe(self, text="Brasil API")
        lf_brasilapi.pack(pady=5, padx=5, fill="x", expand=False)

        self.json_brasilapi = tk.StringVar()
        ttk.Entry(lf_brasilapi, textvariable=self.json_brasilapi).grid(
            row=0, column=0, sticky="ew", padx=5, pady=5
        )
        ttk.Button(lf_brasilapi, text="Buscar", command=self.buscar_brasilapi).grid(
            row=0, column=1, padx=5, pady=5
        )

        lf_brasilapi.columnconfigure(0, weight=1)

        # Arquivo BrasilAPI:
        lf_scrappy = ttk.Labelframe(self, text="Brasil API")
        lf_scrappy.pack(pady=5, padx=5, fill="x", expand=False)

        self.json_scrappy = tk.StringVar()
        ttk.Entry(lf_scrappy, textvariable=self.json_scrappy).grid(
            row=0, column=0, sticky="ew", padx=5, pady=5
        )
        ttk.Button(lf_scrappy, text="Buscar", command=self.buscar_scrappy).grid(
            row=0, column=1, padx=5, pady=5
        )

        lf_scrappy.columnconfigure(0, weight=1)

        # Botão de execução:
        # TODO: Thread para não travar a interface
        ttk.Button(
            self,
            text="Executar",
            command=self.executar,
        ).pack(pady=5, padx=5)

    def buscar_brasilapi(self):
        arquivo = filedialog.askopenfilename(
            title="Arquivo JSON",
            filetypes=[(".json", "*.json")],
        )
        if arquivo:
            self.json_brasilapi.set(arquivo)
            logging.info(f"Arquivo Excel selecionado: {arquivo}")

    def buscar_scrappy(self):
        arquivo = filedialog.askopenfilename(
            title="Arquivo JSON",
            filetypes=[(".json", "*.json")],
        )
        if arquivo:
            self.json_scrappy.set(arquivo)
            logging.info(f"Arquivo Excel selecionado: {arquivo}")

    def executar(self):
        # TODO: Renomear a função para algo mais descritivo

        # TODO: Refatorar as validações para uma função própria
        if not self.json_brasilapi.get():
            logging.error("Nenhum arquivo da BrasilAPI foi selecionado")
            return

        if not self.json_scrappy.get():
            logging.error("Nenhum arquivo do Scrappy foi selecionado")
            return

        # Realizando o merge:
        result = merge_results(self.json_brasilapi.get(), self.json_scrappy.get())

        # Salvando o resultado:
        self.salvar_merge(result)

        # Feedback para o usuário:
        logging.info("Merge realizado com sucesso")
        messagebox.showinfo("Sucesso", "Merge realizado com sucesso")

    def salvar_merge(self, result):
        # TODO: Permitir que o usuário escolha o local de salvamento

        with open(
            file=f"merges/merged-{datetime.now():%Y-%m-%d-%H-%M-%S}.json",
            mode="w",
            encoding="utf-8",
        ) as f:
            json.dump(result, f, ensure_ascii=False)
