import tkinter as tk
from tkinter import ttk

from cepfoliummap.config import initial_config
from cepfoliummap.frames import CepFoliumMapFrame, GeocodeFrame, MergeFrame


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
            "GeoCode": GeocodeFrame(self.notebook),
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
    # Configurações iniciais:
    initial_config()

    # Rodando aplicação:
    app = App()
    app.run()


if __name__ == "__main__":
    main()
