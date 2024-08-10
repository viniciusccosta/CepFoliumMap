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

from cepfoliummap.constants import (
    BRASILAPI_URL,
    COORDENADAS_BRASIL,
    MAX_AT_ONCE,
    REQUESTS_SECOND,
)
from cepfoliummap.geocode import get_coordinates_from_cep

logger = logging.getLogger(__name__)


class CepFoliumMapFrame(tk.Frame):
    # TODO: Criar módulo próprio para as funções de CepFoliumMap e deixar somente a interface gráfica aqui
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master

        # Arquivo Excel:
        lf_excel = ttk.Labelframe(
            self,
            text="Arquivo Excel (cep, grupo, latitude, longitude, icon, color, texto)",
        )
        lf_excel.pack(pady=5, padx=5, fill="x", expand=False)

        lf_excel.columnconfigure(0, weight=1)

        self.arquivo_excel = tk.StringVar()
        ttk.Entry(lf_excel, textvariable=self.arquivo_excel).grid(
            row=0, column=0, sticky="ew", padx=5, pady=5
        )
        ttk.Button(lf_excel, text="Buscar", command=self.buscar_xls).grid(
            row=0, column=1, padx=5, pady=5
        )

        # BrasilAPI (opcional):
        lf_brasilapi = ttk.Labelframe(
            self,
            text="BrasilAPI JSON [opcional]",
        )
        lf_brasilapi.pack(pady=5, padx=5, fill="x", expand=False)

        lf_brasilapi.columnconfigure(0, weight=1)

        ToolTip(
            lf_brasilapi,
            text="Arquivo JSON, no padrão da BrasilAPI, que contém os resultados anteriores, diminuindo a quantidade de consultas necessárias",
        )

        self.arquivo_json = tk.StringVar()
        ttk.Entry(lf_brasilapi, textvariable=self.arquivo_json).grid(
            row=0, column=0, sticky="ew", padx=5, pady=5
        )
        ttk.Button(lf_brasilapi, text="Buscar", command=self.buscar_json).grid(
            row=0, column=1, padx=5, pady=5
        )

        # GeoCode (opcional)
        lf_geocode = ttk.Labelframe(self, text="Geocode API Key [opcional]")
        lf_geocode.pack(pady=5, padx=5, fill="x", expand=False)

        lf_geocode.columnconfigure(1, weight=1)

        self.geocode_var = tk.IntVar(value=0)
        ttk.Checkbutton(
            lf_geocode,
            text="Usar GeoCode",
            variable=self.geocode_var,
            command=self.on_check_api,
        ).grid(row=0, column=0, padx=5, pady=5)

        self.api_key = tk.StringVar()
        self.entry = ttk.Entry(
            lf_geocode,
            textvariable=self.api_key,
            show="*",
            state="disabled",
        )
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.max_request = tk.IntVar(value=1)
        self.spinbox = ttk.Spinbox(
            lf_geocode,
            from_=1,
            to=10,
            textvariable=self.max_request,
            state="disabled",
        )
        self.spinbox.grid(row=0, column=2, padx=5, pady=5)

        # Configurações Gerais:
        lf_settings = ttk.Labelframe(self, text="Configurações Gerais")
        lf_settings.pack(pady=5, padx=5, fill="x", expand=False)

        self.consumir_api = tk.IntVar(value=0)
        ttk.Checkbutton(
            lf_settings,
            text="Consumir API",
            variable=self.consumir_api,
        ).pack(pady=5, padx=5)

        # Botão de execução:
        # TODO: Thread para não travar a interface
        ttk.Button(
            self,
            text="Executar",
            command=lambda: asyncio.run(self.executar()),
        ).pack(pady=5, padx=5)

    # --------------
    def buscar_xls(self):
        arquivo_excel = filedialog.askopenfilename(
            title="Arquivo Excel",
            filetypes=[(".xls", "*.xls")],
        )
        if arquivo_excel:
            self.arquivo_excel.set(arquivo_excel)
            logger.info(f"Arquivo Excel selecionado: {arquivo_excel}")

        # Liberar botão de execução se arquivo arquivo_excel.get() não é None|Vazio

    def buscar_json(self):
        arquivo_json = filedialog.askopenfilename(
            title="Arquivo JSON",
            filetypes=[(".json", "*.json")],
        )
        if arquivo_json:
            self.arquivo_json.set(arquivo_json)
            logger.info(f"Arquivo JSON selecionado: {arquivo_json}")

    def on_check_api(self):
        if self.geocode_var.get():
            self.entry.configure(state="normal")
            self.spinbox.configure(state="normal")
        else:
            self.entry.configure(state="disabled")
            self.spinbox.configure(state="disabled")

    # --------------
    async def executar(self):
        # TODO: Renomear a função para algo mais descritivo

        # TODO: Refatorar as validações para uma função própria
        # Verificando se o arquivo Excel foi selecionado:
        arquivo_excel = self.arquivo_excel.get()
        if not arquivo_excel:
            messagebox.showerror("Erro", "Nenhum arquivo Excel foi selecionado")
            logger.info("Nenhum arquivo Excel foi selecionado")
            return

        # Verificando se o usuário deseja usar a API Key do GeoCode:
        if self.geocode_var.get() and not self.api_key.get():
            messagebox.showerror("Erro", "Nenhuma API Key foi informada")
            logger.info("Nenhuma API Key foi informada")
            return

        # Verificando se o usuário deseja consumir a API:
        if not self.consumir_api.get() and self.arquivo_json.get() == "":
            messagebox.showerror("Erro", "Nenhum arquivo JSON foi selecionado")
            logger.info("Nenhum arquivo JSON foi selecionado")
            return

        # Gerando dataframe a partir de um arquivo Excel:
        dataframe = self.get_dataframe(arquivo_excel)
        consultar_df = dataframe.copy()

        # Lendo arquivo JSON:
        arquivo_json = self.arquivo_json.get()

        if self.consumir_api.get():
            if arquivo_json:
                with open(arquivo_json, "r", encoding="utf-8") as f:
                    # CEPs já consultados (talvez com coordenadas):
                    api_results = json.load(f)

                    # Encontrando CEPs consultados que não possuem coordenadas:
                    ceps_json = set(api_results.keys())
                    ceps_sem_coordenadas = set(
                        {
                            k: v
                            for k, v in api_results.items()
                            if not v.get("location", {}).get("coordinates")
                        }.keys()
                    )

                    # Atualizando dataframe:
                    mask = consultar_df["cep"].apply(
                        lambda x: not (x in ceps_json and x not in ceps_sem_coordenadas)
                    )
                    consultar_df = consultar_df[mask]

            # Consultando CEPs (apenas os que não possuem coordenadas):
            new_results = await self.consultar_ceps(consultar_df)

            # Junção dos resultados:
            if arquivo_json:
                api_results.update(new_results)

            # Salvando resultados em um arquivo JSON:
            self.export_results(api_results)
        else:
            with open(arquivo_json, "r", encoding="utf-8") as f:
                api_results = json.load(f)

        # Inserindo/populando colunas de latitude e longitude no dataframe:
        df_coordenadas = self.populate_dataframe_coordinates(dataframe, api_results)

        # Efetivamente gerando o mapa
        mapa = self.gerar_mapa(df_coordenadas)

        # Salvando mapa
        self.salvar_mapa(mapa)

        # Feedback para o usuário:
        logger.info("Mapa gerado com sucesso")
        messagebox.showinfo("Sucesso", "Mapa gerado com sucesso")

    # --------------
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

    async def consultar_ceps(self, dataframe):
        """
        Função que consome a API do BrasilAPI para obter as coordenadas dos CEPs, com várias requisições assíncronas.

        Args:
            dataframe (pd.DataFrame): DataFrame com todas as colunas necessárias

        Returns:
            json: Dicionário com os resultados da API
        """

        # Agrupando CEPs iguais:
        unique_ceps = list(dataframe["cep"].drop_duplicates().dropna())

        # Consumindo APIs
        tasks = run_all(
            [partial(self.buscar_cep, cep) for cep in unique_ceps],
            max_at_once=MAX_AT_ONCE,
            max_per_second=REQUESTS_SECOND,
        )
        results = await tasks

        # Formatando resultados:
        results = {r["cep"]: r for r in results if r}

        # Retornando resultado:
        return results

    async def buscar_cep(self, cep):
        """
        Função que efetivamente consome a API do BrasilAPI para obter as coordenadas de um CEP de forma assíncrona.
        """

        # BrasilAPI:
        try:
            async with AsyncClient(base_url=BRASILAPI_URL, timeout=60) as client:
                logger.debug(f"Consultando CEP no BrasilAPI: {cep}")
                brasilapi_response = await client.get(str(cep))
        except Exception as e:
            logger.exception(e)
            logger.error(f"Error ao tentar consumir BrasilAPI para o CEP {cep}")
            return {}

        # GeoCode (se necessário):
        if brasilapi_response.status_code == 200:
            brasilapi_json = brasilapi_response.json()

            if "latitude" in brasilapi_json["location"]["coordinates"]:
                logging.debug(
                    f"CEP {cep} possui coordenadas: {brasilapi_json['location']['coordinates']}"
                )
                return brasilapi_json

            # TODO: Refatorar para uma função própria:
            logger.debug(f"CEP {cep} não possui coordenadas | Consultando GeoCode")
            lat, lng = await get_coordinates_from_cep(cep, self.api_key.get())

            # Atualizando JSON:
            if lat and lng:
                logger.debug(f"Atualizando coordenadas do CEP {cep}: ({lat}, {lng})")
                brasilapi_json["location"]["coordinates"]["latitude"] = lat
                brasilapi_json["location"]["coordinates"]["longitude"] = lng

            # Retornando resultado:
            return brasilapi_json

        # Resultado padrão:
        logger.warning(f"CEP {cep} não encontrado na BrasilAPI")
        return {}

    def populate_dataframe_coordinates(self, dataframe, api_results):
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
                logger.warning(f"Coordenadas não encontradas para o CEP {cep}", e)
            except Exception as e:
                logger.exception(e)
                logger.error(f"Erro ao tentar atualizar coordenadas do CEP {cep}")

        return df_coordenadas

    def export_results(self, result):
        # TODO: Com a unificação dos Frames esse arquivo não deveria mais ser salvo em "brasilapi"
        with open(
            file=f"consultas/{datetime.now():%Y-%m-%d-%H-%M-%S}.json",
            mode="w",
            encoding="utf8",
        ) as file:
            json.dump(result, file, ensure_ascii=False)

    def gerar_mapa(self, dataframe):
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
                        logger.warning(
                            f"CEP {cep} não possui localização: ({lat}, {lng})"
                        )
                except Exception as e:
                    logger.exception(e)
                    logger.error(f"Erro ao tentar adicionar marcador ao mapa: {cep}")

        # Quantidade de CEPs que não foram adicionados ao mapa:
        logger.info(
            f"Um total de {cnt_not_marked} marcadores não foram adicionados ao mapa"
        )

        # Controlador:
        folium.LayerControl(collapsed=False).add_to(mapa)

        return mapa

    def salvar_mapa(self, mapa):
        # TODO: Permitir que o usuário escolha o local de salvamento

        filename = f"mapas/{datetime.now():%Y-%m-%d-%H-%M-%S}.html"
        mapa.save(filename)
