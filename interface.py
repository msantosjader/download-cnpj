import asyncio
from nicegui import ui, run
from datetime import datetime
from settings import load_settings, save_settings, restore_default_settings
from folder_picker import LocalFolderPicker
from data_rfb import atualizar_rfb_data, check_data_download
from data_download import download_manager


def render_layout(content_function):
    settings = load_settings()
    drawer = None

    async def pick_folder() -> None:
        folder = await LocalFolderPicker('~')
        if folder is not None:
            folder_ui.value = folder

    with ui.header(elevated=True).style('background-color: #00205B; color: white').classes(
            'items-center justify-between'):
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('Download Base CNPJ').classes('text-2xl font-bold tracking-wide')
            with ui.row().classes('gap-x-2 items-center no-wrap'):
                ui.button(icon='refresh', on_click=lambda:
                ui.notify("Download em andamento", type='warning')
                if download_manager.running else ui.navigate.to('/')
                          ).props('flat color=white size="lg"')
                ui.button(icon='settings', on_click=lambda: drawer.toggle()).props('flat color=white size="lg"')
    with ui.right_drawer().style('background-color: #d7e3f4').classes('items-center') as drawer:
        with ui.card().classes('w-full items-center relative'):
            ui.button(icon='close', on_click=lambda: drawer.toggle()) \
                .props('flat round dense').classes('absolute top-2 right-2')
            ui.label('Downloads').classes('text-lg font-medium')

            with ui.row().classes('w-full items-center'):
                with ui.card().classes('w-full'):
                    ui.label("Salvar em:").classes('font-bold')
                    folder_ui = ui.textarea(
                        placeholder="Local",
                        value=settings.get("download_path", ""),
                    ).classes('w-full').props('rows=3 dense outlined')
                    ui.button('Selecionar pasta', icon='folder_open', on_click=pick_folder).props('size="md"')

                with ui.card().classes('w-full'):
                    ui.label("URL Receita Federal:").classes('font-bold')
                    url_ui = ui.textarea(
                        placeholder="Dados Abertos CNPJ",
                        value=settings.get("rfb_url", ""),
                    ).classes('w-full').props('rows=3 dense outlined')

            with ui.column().classes('w-full'):
                with ui.row().classes('w-full gap-2 flex flex-nowrap'):
                    ui.button('Salvar', icon='save', color='primary',
                              on_click=lambda: save_settings(folder_ui.value, url_ui.value)) \
                        .props('size="md"').classes('flex-grow')
                    ui.button(icon='settings_backup_restore', color='green',
                              on_click=lambda: set_default_settings()) \
                        .props('size="md"').classes('flex-shrink-0')

                    def set_default_settings():
                        restore_default_settings(notify=True)
                        new_settings = load_settings()
                        folder_ui.value = new_settings.get("download_path", "")
                        url_ui.value = new_settings.get("rfb_url", "")

    with ui.column().classes('w-full items-center'):
        content_function()


@ui.page('/')
def download_page():
    def content():
        ui.label('Download da Base de Dados').style('color: #00205B').classes('text-2xl font-bold')

        file_map = {}
        tree = None
        task_cards = []

        with ui.card().classes('w-full max-w-4xl mx-auto'):
            with ui.row().classes('w-full gap-4'):
                with ui.card().classes('flex-1 p-2 items-center') as tree_card:
                    ui.label('Arquivos da Receita Federal').classes('text-lg font-medium mb-2  text-center')
                    spinner = ui.spinner('dots').props('size="xl"')
                    loading_label = ui.label('Verificando a base de dados online...').classes('mt-2 text-gray')
                with ui.card().classes('flex-1 p-2 items-stretch'):
                    ui.label('Downloads em andamento').classes('text-lg font-medium mb-2  text-center')
                    with ui.row().classes('w-full gap-2 flex-nowrap items-center'):
                        ui.button('Cancelar Todos', icon='cancel', color='red', on_click=download_manager.cancel_all) \
                            .classes('flex-grow')

                        def retry_failed():
                            for task in download_manager.tasks:
                                if task.status == "failed":
                                    task.set_status("queued")
                                    if task.ui_elements.get('status'):
                                        task.ui_elements['status'].text = 'Na fila'
                            asyncio.create_task(download_manager.start_downloads())

                        ui.button(icon='restart_alt', color='orange', on_click=retry_failed) \
                            .classes('flex-shrink-0')

                        def refresh_cards():
                            download_manager.clear_completed()
                            for card, task in list(task_cards):
                                if task.status in ("completed", "failed", 'cancelled'):
                                    card.delete()
                                    task_cards.remove((card, task))

                        ui.button(icon='cleaning_services', color='green', on_click=refresh_cards) \
                            .classes('flex-shrink-0')

                    download_container = ui.column().classes('space-y-1') \
                        .style('max-height: 400px; overflow-y: auto;')

        async def build_tree():
            nonlocal file_map, tree
            settings = load_settings()
            rfb_data = settings.get('rfb_available', {})
            tree_data = []

            for month_key in sorted(rfb_data.keys(), key=lambda x: datetime.strptime(x, '%Y-%m'), reverse=True):
                files = rfb_data[month_key]
                display_label = datetime.strptime(month_key, '%Y-%m').strftime('%m/%Y')
                total_bytes = sum(int(item.get('size', 0)) for item in files)
                total_gb = total_bytes / (1024 ** 3)
                children = []
                encontrados = 0

                for file in files:
                    size = int(file['size'])
                    node_id = file['id']
                    is_ok = check_data_download(settings.get("download_path", ""), month_key, file['name'], size)
                    file_map[node_id] = {
                        'download_link': file['download_link'],
                        'month_key': month_key,
                        'filename': file['name'],
                        'size': size
                    }
                    if is_ok:
                        encontrados += 1
                    label = f"{file['name']} ({size / 1024 ** 2:.1f} MB)"
                    children.append({
                        'id': node_id,
                        'label': label,
                        'icon': 'check_circle' if is_ok else 'error',
                        'icon_color': 'green' if is_ok else 'red'
                    })

                icon, icon_color = ('check_circle', 'green') if encontrados == len(files) else \
                                   ('error', 'red') if encontrados == 0 else \
                                   ('warning', 'orange')
                display_label = f"{display_label} ({total_gb:.2f} GB)"

                tree_data.append({
                    'id': month_key,
                    'label': display_label,
                    'icon': icon,
                    'icon_color': icon_color,
                    'children': children
                })

            tree_card.clear()
            with tree_card:
                ui.label('Arquivos da Receita Federal').classes('text-lg font-medium mb-2')
                ui.button('Baixar Selecionados', icon='download', color='primary',
                          on_click=lambda: asyncio.create_task(
                              ui.notify("Download em andamento", type='warning')
                              if download_manager.running else start_download()
                          )).classes('w-full mb-4')
                tree = ui.tree(tree_data,
                               label_key='label',
                               tick_strategy='leaf',
                               on_tick=lambda e: setattr(tree, 'selected', e.value)
                               ).classes('w-full text-lg border rounded-md').props('html-label').style('max-height: 385px; overflow-y: auto;')

        async def start_download():
            download_container.clear()
            selected_nodes = getattr(tree, 'selected', [])
            if not selected_nodes:
                with download_container:
                    ui.notify('Nenhum arquivo selecionado para download', type='warning')
                return

            for node_id in selected_nodes:
                info = file_map.get(node_id)
                if info:
                    task = download_manager.add_task(
                        info['download_link'], info['month_key'], info['filename'], info['size'])

                    task_cards.append(None)  # placeholder

                    with download_container:
                        with ui.card().classes('w-full p-3 items-stretch').style('min-width: 100%;') as card:
                            task_cards[-1] = (card, task)
                            with ui.row().classes('items-center gap-2'):
                                task.ui_elements['status_icon'] = ui.icon('hourglass_empty').props('size=sm')
                                ui.label(f"{info['filename']} ({info['month_key']})").classes('font-bold ml-2')

                                cancel_btn = ui.button('Cancelar', icon='cancel', color='red') \
                                    .props('flat size=sm').classes('absolute top-2 right-2')
                                task.ui_elements['cancel_btn'] = cancel_btn
                                cancel_btn.on('click', lambda e, t=task, b=cancel_btn: (
                                    t.cancel_event.set(), b.set_visibility(False)))

                            task.ui_elements['progress'] = ui.linear_progress(value=0, show_value=False,
                                                                              color='#00205B') \
                                .classes('w-full mt-2')
                            with ui.row().classes('justify-between items-center mt-2'):
                                task.ui_elements['status'] = ui.label('Na fila')

                    # Reaplica o status para atualizar a UI se o task já estiver concluído
                    task.set_status(task.status)

            asyncio.create_task(download_manager.start_downloads())
            await build_tree()

        async def load_data():
            nonlocal spinner, loading_label

            await asyncio.sleep(0.1)
            await run.io_bound(atualizar_rfb_data, False)
            with tree_card:
                ui.notify("Informações atualizadas!", type='positive')
                spinner.delete()
                loading_label.delete()
            await build_tree()

        ui.timer(0.1, lambda: asyncio.create_task(load_data()), once=True)

    render_layout(content)