import os
import sys
from settings import check_settings_file, ENV, SETTINGS_FILE_PATH
from logs import Logger


if ENV != 'dev':
    # Cria o caminho completo para o arquivo de log, ao lado do settings.json
    log_path = os.path.join(os.path.dirname(SETTINGS_FILE_PATH), 'logs.txt')
    sys.stdout = Logger(log_path)


# roda sempre, mesmo em import — cria/atualiza settings.json
check_settings_file()

from nicegui import ui, native
import interface  # noqa: F401

# só sobe o servidor se for executado como script/entrypoint
if __name__ == "__main__":
    ui.run(
        native=True,
        reload=False,
        port=native.find_open_port(),
        window_size=(1024, 800),
        title='Download Base CNPJ',
        favicon='https://i.ibb.co/PZXFSDp2/icons8-baixar-16.png'
    )

