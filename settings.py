import os
import sys
import json
from nicegui import ui

APP_NAME = "DownloadCNPJ"
ENVIRONMENT = "dev" # dev / prod

#DATA_DOWNLOAD CONSTANTS
MAX_RETRIES = 100 # Máximo de tentativas para baixar um arquivo
CHUNK_TIMEOUT = 60 # Tempo máximo para baixar um chunk de um arquivo
MAX_CONCURRENT_DOWNLOADS = 10 # Número máximo de downloads concorrentes
CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/103.0.0.0 Safari/537.36"
] # Lista de User-Agents para usar no download

# DATA_RFB CONSTANTS
NUM_RECENT_MONTHS = 1 # Número de meses recentes a considerar
TIME_CHECK_INTERVAL = 3600  # 1 hora em segundos

def get_settings_path():
    # dev coloca o settings no diretório do projeto
    if ENVIRONMENT == "dev":
        return os.path.join(os.path.dirname(__file__), 'settings.json')

    # senão coloca o settings na pasta de configuração do sistema
    if sys.platform == "win32":
        # Ex: C:\Users\<usuario>\AppData\Local\DownloadCNPJ
        base_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), APP_NAME)
    else:
        # Ex: ~/.config/DownloadCNPJ
        base_dir = os.path.join(os.path.expanduser("~/.config"), APP_NAME)

    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "settings.json")

SETTINGS_FILE_PATH = get_settings_path() # Onde criar/salvar o arquivo de settings
DEFAULT_DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Downloads", "DadosCNPJ") # Caminho padrão para downloads
DEFAULT_RFB_URL = "https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/" # URL dos recursos da RFB
DEFAULT_SETTINGS = {
    "download_path": DEFAULT_DOWNLOAD_PATH,
    "rfb_last_check": "",
    "rfb_url": DEFAULT_RFB_URL,
    "rfb_available": {}
} # Settings padrão

def check_settings_file():
    if not os.path.exists(SETTINGS_FILE_PATH):
        restore_default_settings()
        print(f"Arquivo '{SETTINGS_FILE_PATH}' criado com os settings padrão.")

def restore_default_settings(notify=False):
    current_settings = {}
    if os.path.exists(SETTINGS_FILE_PATH):
        with open(SETTINGS_FILE_PATH, 'r') as file:
            current_settings = json.load(file)

    current_settings.update(DEFAULT_SETTINGS)

    with open(SETTINGS_FILE_PATH, 'w') as file:
        json.dump(current_settings, file, indent=4)  # type: ignore

    if notify:
        ui.notify("Configurações restauradas!", type='positive')

def load_settings():
    if os.path.exists(SETTINGS_FILE_PATH):
        with open(SETTINGS_FILE_PATH, 'r') as file:
            return json.load(file)
    return DEFAULT_SETTINGS

def save_settings(download_path, rfb_url):
    current_settings = {}
    if os.path.exists(SETTINGS_FILE_PATH):
        with open(SETTINGS_FILE_PATH, 'r') as file:
            current_settings = json.load(file)

    current_settings.update({
        "download_path": download_path,
        "rfb_url": rfb_url
    })

    with open(SETTINGS_FILE_PATH, 'w') as file:
        json.dump(current_settings, file, indent=4)  # type: ignore

    ui.notify("Configurações salvas!", type='positive')
