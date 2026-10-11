import os
import torch
import pandas as pd
from transformers import pipeline


caminho_arquivo = 'yugioh-ccd-2025SEP12-163128.csv'

candidate_labels = [
    "ATK or DEF modification / debuff",   
    "battle protection or trap card",     
    "negate effect or activation",        
    "destroy monster on field",           
    "special summon monster",             
    "draw cards from deck",
    "add from deck to hand" 
]

# Cache singleton para evitar recarregar o modelo a cada análise
_classifier_instance = None
_classifier_device = None


def get_default_device():
    """Detecta se CUDA está disponível (0) ou usa CPU (-1)."""
    return 0 if torch.cuda.is_available() else -1


def carregar_dados(caminho=None):
    """Carrega a base de dados de cartas CSV."""
    caminho = caminho or caminho_arquivo
    if not os.path.isabs(caminho):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        caminho_abs = os.path.join(base_dir, caminho)
        if os.path.exists(caminho_abs):
            caminho = caminho_abs
    return pd.read_csv(caminho)


def carregar_classificador(device=None, force_reload=False):
    """Carrega o pipeline zero-shot classification mantendo instância única em memória."""
    global _classifier_instance, _classifier_device
    if device is None:
        device = get_default_device()

    if _classifier_instance is None or _classifier_device != device or force_reload:
        device_name = "GPU" if (isinstance(device, int) and device >= 0) else "CPU"
        print(f"Carregando o modelo de IA no dispositivo {device_name} (device={device})...")
        _classifier_instance = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=device
        )
        _classifier_device = device
    return _classifier_instance


def classificar_efeito(texto_efeito, labels=None, device=None, classificador=None):
    """Classifica o texto do efeito de uma carta de acordo com os rótulos de candidato."""
    if not texto_efeito or not str(texto_efeito).strip():
        return {"labels": [], "scores": [], "sequence": ""}

    if labels is None:
        labels = candidate_labels

    if classificador is None:
        classificador = carregar_classificador(device=device)

    resultado = classificador(str(texto_efeito), labels)
    return resultado


# Carregamento preguiçoso do DataFrame para compatibilidade
_df_cached = None

def get_df():
    """Retorna o DataFrame carregado em memória."""
    global _df_cached
    if _df_cached is None:
        _df_cached = carregar_dados()
    return _df_cached


if __name__ == "__main__":
    df = carregar_dados()
    print("Carregando o modelo de IA...")
    classifier = carregar_classificador()

    # colocar a linha das cartas
    texto_exemplo = str(df['description'].iloc[0])
    nome_exemplo = str(df['name'].iloc[0])

    resultado = classifier(texto_exemplo, candidate_labels)

    print(f"--- Carta: {nome_exemplo} ---")
    print(f"Descrição: {texto_exemplo}\n")
    print("Classificação da IA:")
    for label, score in zip(resultado['labels'], resultado['scores']):
        print(f"-> {label}: {score*100:.2f}%")

    # Analise de sentimento e classificação de efeitos baseado em YuGiOh!

    # REFERENCIA--------------------------------------------------------------------------------------------------------------------------------------
    # IA Utilizada no Hugginface: https://huggingface.co/facebook/bart-large-mnli
    # Base de dados utilizada do Yugioh: https://www.kaggle.com/datasets/hammadus/yugioh-full-card-database-index-august-1st-2025?resource=download
    # REFERENCIA--------------------------------------------------------------------------------------------------------------------------------------

    # Facebook bart large mnli, e um modelo voltado para o processamento de linguagem natural, especializado em entender relação entre frases e classificar textos.
    # basicamente do codigo, o nosso arquivo csv e nada mais do que linhas e colunas, que o python le pelo pandas.
    # ele isola o nome e a description de cada carta e manda esse texto para a GPU.
    # a IA pega as categorias (candidate_labels), compara com o efeito e calcula as porcentagens.
    # no final, o código só exibe a carta e quais categorias tiveram maior probabilidade.
