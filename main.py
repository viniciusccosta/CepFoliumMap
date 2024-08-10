import tkinter as tk
from tkinter import ttk

from cepfoliummap.config import initial_config
from cepfoliummap.frames import CepFoliumMapFrame


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.minsize(600, 310)
        self.maxsize(1200, 310)
        self.title("Cep Folium Map")

        # Notebook:
        self.notebook = ttk.Notebook(self)

        # Frames
        self.frames = {
            "Folium Map": CepFoliumMapFrame(self.notebook),
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
