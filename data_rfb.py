import re
import json
import datetime
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from settings import SETTINGS_FILE, DEFAULT_RFB_URL, load_settings

# Número de meses recentes a considerar
NUM_RECENT = 1

# Sessão para reutilizar conexões HTTP
session = requests.Session()


def parse_key(key: str):
    """
    Converte uma chave no formato "YYYY-MM/" para uma tupla (YYYY, MM)
    para permitir comparações cronológicas.
    """
    key = key.rstrip('/')
    try:
        year, month = key.split('-')
        return int(year), int(month)
    except ValueError:
        return 0, 0


def get_threshold(current_data: dict, num_recent: int):
    """
    Retorna a chave threshold para verificação. Se houver pelo menos num_recent
    registros, retorna a terceira mais recente; caso contrário, None.
    """
    if not current_data:
        return None
    keys = sorted(current_data.keys(), key=parse_key)
    if len(keys) >= num_recent:
        return keys[-num_recent]
    return None


def obter_conteudo(url: str) -> BeautifulSoup:
    """
    Faz requisição GET e retorna BeautifulSoup do HTML.
    """
    resp = session.get(url)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, 'html.parser')


def get_cnpj_zip_files() -> dict:
    """
    Coleta arquivos ZIP de diretórios "YYYY-MM/" na URL da RFB,
    filtrando somente os meses novos (>= threshold) e extraindo
    nome, last-modified e size de cada arquivo.

    Retorna dict: { 'YYYY-MM/': [ { 'name':..., 'last_modified':..., 'size':... }, ... ], ... }
    """
    settings_data = load_settings()
    rfb_url = settings_data.get("rfb_url", DEFAULT_RFB_URL)

    current_rfb_avail = settings_data.get("rfb_available", {})
    threshold = get_threshold(current_rfb_avail, NUM_RECENT)

    print("Etapa 1: Coletando pastas de mês-ano...")
    soup_base = obter_conteudo(rfb_url)
    meses_ano = [
        tag.get('href') for tag in soup_base.find_all('a')
        if tag.get('href') and re.match(r'^\d{4}-\d{2}/$', tag.get('href'))
    ]
    meses_ano = sorted(meses_ano, key=parse_key)
    if threshold is not None:
        meses_ano = [m for m in meses_ano if parse_key(m) >= parse_key(threshold)]
    if not meses_ano and current_rfb_avail:
        print("Nenhum novo mês encontrado; mantendo registros existentes.")
        return {}

    keywords = [
        "cnaes", "empresas", "estabelecimentos", "movitos",
        "municipios", "naturezas", "paises", "qualificacoes",
        "simples", "socios"
    ]

    novos_arquivos_por_mes = {}
    print("Etapa 2: Processando pastas e filtrando arquivos zip...")
    for mes in meses_ano:
        mes_key = mes.rstrip('/')
        print(f"Processando a pasta: {mes_key}")
        url_mes = urljoin(rfb_url, mes)
        soup_mes = obter_conteudo(url_mes)

        file_entries = []  # lista de dicts com metadata parcial
        missing = []       # lista de (idx, file_url) para HEAD

        for tag in soup_mes.find_all('a'):
            href = tag.get('href')
            if not href or not href.lower().endswith('.zip'):
                continue
            lower_nome = href.lower()
            if not any(kw in lower_nome for kw in keywords):
                continue

            # Tenta extrair metadata do listing HTML
            last_mod = None
            size = None
            # Em listagens Apache, texto após o <a> contém data e tamanho
            sibling = tag.next_sibling
            if sibling and isinstance(sibling, str):
                parts = sibling.strip().split()
                if len(parts) >= 3:
                    last_mod = f"{parts[0]} {parts[1]}"
                    size = parts[2]

            entry = { 'name': href, 'last_modified': last_mod, 'size': size }
            file_entries.append(entry)

            # se faltou algum dado, agendar HEAD
            if last_mod is None or size is None:
                file_url = urljoin(url_mes, href)
                missing.append((len(file_entries) - 1, file_url))

        # Executa HEADs em paralelo para preencher metadata faltante
        if missing:
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_idx = {
                    executor.submit(session.head, url, allow_redirects=True): idx
                    for idx, url in missing
                }
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        head = future.result()
                        file_entries[idx]['last_modified'] = head.headers.get('Last-Modified')
                        file_entries[idx]['size'] = head.headers.get('Content-Length')
                    except Exception as e:
                        print(f"Erro ao obter HEAD para {missing[idx][1]}: {e}")

        novos_arquivos_por_mes[mes_key] = file_entries

    print("\nResumo final de arquivos extraídos por mês:")
    for mes, arquivos in novos_arquivos_por_mes.items():
        print(f"{mes}: {arquivos}")
    return novos_arquivos_por_mes


def update_latest_rfb_available(dados_novos: dict):
    """
    Atualiza 'rfb_available' e 'rfb_last_check' no settings.json,
    combinando registros antigos e novos (>= threshold).
    Também adiciona 'id' único e 'download_link' para cada arquivo.
    """
    current_settings = load_settings()
    current_rfb_avail = current_settings.get("rfb_available", {})
    rfb_url_base = current_settings.get("rfb_url", DEFAULT_RFB_URL)
    threshold = get_threshold(current_rfb_avail, NUM_RECENT)

    combined = current_rfb_avail.copy()
    for key, arquivos in dados_novos.items():
        clean_key = key.rstrip('/')  # garante formato AAAA-MM
        if threshold is None or parse_key(clean_key) >= parse_key(threshold):
            # adiciona metadados aos arquivos
            for i, file in enumerate(arquivos):
                file['id'] = f'{clean_key}_{i}'
                file['download_link'] = urljoin(rfb_url_base, f'{clean_key}/{file["name"]}')
            combined[clean_key] = arquivos

    current_settings["rfb_available"] = combined
    current_settings["rfb_last_check"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(SETTINGS_FILE, 'w') as file:
        json.dump(current_settings, file, indent=4)  # type: ignore

    print("settings.json atualizado com novos registros e metadata.")
    print(f"Última verificação: {current_settings['rfb_last_check']}")


def atualizar_rfb_data(manual: bool = False) -> bool:

    """
    Atualiza dados da RFB:
      - Se manual=True, força a atualização e mostra "Aguarde..." no início.
      - Se manual=False, só atualiza se tiver passado mais de 1h da última verificação.

    Retorna True se a atualização rodou, False caso tenha sido pulada.
    """

    # Se não for manual, verifica intervalo de 1h
    if not manual:
        settings = load_settings()
        last_check = settings.get("rfb_last_check")
        if last_check:
            try:
                last_time = datetime.datetime.strptime(last_check, "%Y-%m-%d %H:%M:%S")
                diff_h = (datetime.datetime.now() - last_time).total_seconds() / 3600
                if diff_h < 1:
                    print(f"Última verificação há {diff_h:.2f}h. Aguardar 1 hora.")
                    return False
            except (ValueError, TypeError):
                print("Formato de data inválido, forçando atualização.")

    # Executa a coleta de novos arquivos
    novos = get_cnpj_zip_files()
    if novos:
        update_latest_rfb_available(novos)

    return True


def check_data_download(download_path: str, month_key: str, file_name: str, expected_size: int) -> bool:
    path = Path(download_path) / month_key / file_name
    return path.exists() and path.stat().st_size == expected_size


if __name__ == "__main__":
    atualizar_rfb_data(manual=True)
