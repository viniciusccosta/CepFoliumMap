import json

from tkinter  import filedialog, messagebox
from datetime import datetime

from app import gerar_localizacoes

# ===========================================================
def main():
    # Lendo arquivos:
    app_file     = filedialog.askopenfilename(title="Resultado da API", filetypes=[('JSON', '*.json')])
    scrappy_file = filedialog.askopenfilename(title="Resultado do Scrappy", filetypes=[('JSON', '*.json')])
    
    if not(app_file and scrappy_file):
        messagebox.showerror('Erro', 'Necessário informar os 2 arquivos')
        return    
    
    app_results     = json.load(open(app_file)    , )
    scrappy_results = json.load(open(scrappy_file), )
    
    # Gerando objetos "Localização"
    localizacoes = gerar_localizacoes(app_results)
    
    # Atualizando coordenadas das localizações que não possuem latitude e longitude:
    for l in localizacoes:
        if not(l.latitude and l.longitude):
            if scrappy_results.get(l.cep):    # Existe esse CEP no resultado do scrappy e possui valores
                l.latitude  = scrappy_results[l.cep].get('latitude')    # Caso "scrappy_result[cep]" não possua latitude, simplesmente não fará diferença
                l.longitude = scrappy_results[l.cep].get('longitude')   # Caso "scrappy_result[cep]" não possua longitude, simplesmente não fará diferença
                
    # Salva resultado:
    result = [l.to_json() for l in localizacoes]
    with open(f'merge-{datetime.now():%Y-%m-%d-%H-%M-%S}.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False)

# ===========================================================
if __name__ == "__main__":
    main()
