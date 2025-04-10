import os
import json
from nicegui import ui


# Define paths e valores default
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')
DEFAULT_DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Downloads", "DadosCNPJ")
DEFAULT_RFB_URL = "https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/"

DEFAULT_SETTINGS = {
    "download_path": DEFAULT_DOWNLOAD_PATH,
    "rfb_last_check": "",
    "rfb_url": DEFAULT_RFB_URL,
    "rfb_available": {}
}

def check_settings_file():
    if not os.path.exists(SETTINGS_FILE):
        # Abre o arquivo em modo de escrita e grava o conteúdo de DEFAULT_SETTINGS em formato JSON
        restore_default_settings()
        print(f"Arquivo '{SETTINGS_FILE}' criado com os settings padrão.")


def restore_default_settings(notify=False):
    # Carrega as configurações atuais, se existirem, ou inicia com um dicionário vazio
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as file:
            current_settings = json.load(file)
    else:
        current_settings = {}

    # Atualiza somente as chaves definidas em DEFAULT_SETTINGS
    current_settings.update(DEFAULT_SETTINGS)

    # Salva as configurações atualizadas de volta no arquivo
    with open(SETTINGS_FILE, 'w') as file:
        json.dump(current_settings, file, indent=4)  # type: ignore

    if notify:
        ui.notify("Configurações restauradas!", type='positive')


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as file:
            return json.load(file)
    return DEFAULT_SETTINGS


def save_settings(download_path, rfb_url):
    # Tenta carregar as configurações atuais; se não existir, inicia com um dicionário vazio
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as file:
            current_settings = json.load(file)
    else:
        current_settings = {}

    # Atualiza somente as chaves desejadas, mantendo as que já existirem, como "rfb_available"
    current_settings.update({
        "download_path": download_path,
        "rfb_url": rfb_url
    })

    # Salva o dicionário atualizado de volta no arquivo
    with open(SETTINGS_FILE, 'w') as file:
        json.dump(current_settings, file, indent=4)  # type: ignore

    ui.notify("Configurações salvas!", type='positive')



