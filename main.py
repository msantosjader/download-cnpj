# main.py
from settings import check_settings_file

# roda sempre, mesmo em import — cria/atualiza settings.json
check_settings_file()

from nicegui import ui
import interface  # noqa: F401

# só sobe o servidor se for executado como script/entrypoint
if __name__ == "__main__":
    ui.run(
        native=True,
        reload=False,
        window_size=(1024, 786),
        title='Download CNPJ',
        favicon='https://i.ibb.co/PZXFSDp2/icons8-baixar-16.png'
    )

