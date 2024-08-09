import logging
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk

from decouple import config
from rich.logging import RichHandler

from cepfoliummap.frames import CepFoliumMapFrame, MergeFrame, ScrappyFrame


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("600x250")
        self.title("Cep Folium Map")

        # Notebook:
        self.notebook = ttk.Notebook(self)

        # Frames
        self.frames = {
            "Folium Map": CepFoliumMapFrame(self.notebook),
            "Scrappy": ScrappyFrame(self.notebook),
            "Merge": MergeFrame(self.notebook),
        }

        # Adicionando frames ao notebook:
        for name, frame in self.frames.items():
            self.notebook.add(frame, text=name)

        # Adicionando notebook ao app:
        self.notebook.pack(expand=True, fill="both")

    def run(self):
        self.mainloop()


def main():
    # Criando diretórios:
    Path("mapas/").mkdir(parents=True, exist_ok=True)
    Path("brasilapi/").mkdir(parents=True, exist_ok=True)
    Path("logs/").mkdir(parents=True, exist_ok=True)
    Path("scrapps/").mkdir(parents=True, exist_ok=True)
    Path("merges/").mkdir(parents=True, exist_ok=True)

    # Configurando logging:
    file_handler = logging.FileHandler(
        filename=f"logs/{datetime.now():%Y-%m-%d-%H-%M-%S}.log",
        mode="w",
        encoding="utf-8",
    )
    console_handler = RichHandler(rich_tracebacks=True)

    logging.basicConfig(
        level=config("LOGGING_LEVEL", logging.INFO),
        encoding="utf-8",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            file_handler,
            console_handler,
        ],
    )

    # Rodando aplicação:
    app = App()
    app.run()


if __name__ == "__main__":
    main()
