import os
import asyncio
import aiohttp
import aiofiles
import time
from typing import Dict, List, Optional
from settings import load_settings


def format_size(bytes_size: float) -> str:
    if bytes_size >= 1024 ** 3:
        return f"{bytes_size / 1024 ** 3:.2f} GB"
    elif bytes_size >= 1024 ** 2:
        return f"{bytes_size / 1024 ** 2:.2f} MB"
    elif bytes_size >= 1024:
        return f"{bytes_size / 1024:.2f} KB"
    else:
        return f"{bytes_size} bytes"


def format_time(seconds: float) -> str:
    if seconds >= 3600:
        hours = int(seconds // 3600)
        return f"{hours} hora(s) restante(s)"
    elif seconds >= 60:
        minutes = int(seconds // 60)
        return f"{minutes} min restante(s)"
    else:
        return f"{int(seconds)} seg restante(s)"


class DownloadTask:
    def __init__(self, url: str, dest_path: str, file_size: int, month_key: str, filename: str):
        self.url = url
        self.dest_path = dest_path
        self.file_size = file_size
        self.month_key = month_key
        self.filename = filename
        self.progress = 0
        self.status = "queued"
        self.ui_elements: Dict = {}
        self.cancel_event = asyncio.Event()
        self.error_message: Optional[str] = None
        self.start_time: Optional[float] = None

    def update_progress(self, chunk_size: int):
        now = time.monotonic()
        if self.start_time is None:
            self.start_time = now

        self.progress += chunk_size
        elapsed = now - self.start_time
        speed = self.progress / elapsed if elapsed > 0 else 0
        remaining = max(self.file_size - self.progress, 0)
        eta = remaining / speed if speed > 0 else None

        percent = min(100, int(self.progress * 100 / self.file_size))

        if self.ui_elements.get('progress'):
            self.ui_elements['progress'].value = percent / 100
            self.ui_elements['progress'].props(f'label="{percent}%"')

        if self.ui_elements.get('status'):
            downloaded = format_size(self.progress)
            total = format_size(self.file_size)
            speed_str = format_size(speed) + '/s'
            eta_str = format_time(eta) if eta else "Calculando..."
            self.ui_elements['status'].text = f"{speed_str} — {downloaded} de {total}, {eta_str}"

    def set_status(self, status: str, error: str = None):
        self.status = status
        self.error_message = error
        icon = None
        if status == "queued":
            icon = ('hourglass_empty', 'gray')
        elif status == "downloading":
            icon = ('cloud_download', 'blue')
        elif status == "completed":
            icon = ('check_circle', 'green')
        elif status == "failed":
            icon = ('error', 'red')

        if self.ui_elements.get('status_icon') and icon:
            self.ui_elements['status_icon'].props(f"name={icon[0]} color={icon[1]}")
        if status == "failed" and error and self.ui_elements.get('status'):
            self.ui_elements['status'].text = f"{error}"


class DownloadManager:
    def __init__(self):
        self.tasks: List[DownloadTask] = []
        self.max_concurrent_downloads = 3
        self.semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
        self.running = False

    def add_task(self, url: str, month_key: str, filename: str, file_size: int) -> DownloadTask:
        settings = load_settings()
        download_path = settings.get("download_path", "")
        month_dir = os.path.join(download_path, month_key)
        os.makedirs(month_dir, exist_ok=True)
        dest_path = os.path.join(month_dir, filename)
        task = DownloadTask(url, dest_path, file_size, month_key, filename)
        self.tasks.append(task)
        return task

    async def download_file(self, task: DownloadTask):
        if task.cancel_event.is_set():  # <- impede execução se já estiver cancelado
            task.set_status("failed", "Cancelado")
            return

        task.set_status("downloading")
        task.start_time = time.monotonic()
        timeout = aiohttp.ClientTimeout(total=300)
        for attempt in range(3):
            try:
                async with self.semaphore:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(task.url) as response:
                            if response.status != 200:
                                raise aiohttp.ClientError(f"HTTP {response.status}")
                            # caminho do arquivo fora do with
                            file_path = task.dest_path
                            async with aiofiles.open(file_path, 'wb') as f:
                                while True:
                                    if task.cancel_event.is_set():
                                        break
                                    chunk = await response.content.read(1024 * 1024)
                                    if not chunk:
                                        break
                                    await f.write(chunk)
                                    task.update_progress(len(chunk))

                    if task.cancel_event.is_set():
                        task.set_status("failed", "Cancelado")
                        await asyncio.sleep(0.1)  # pequena pausa para garantir que o arquivo seja liberado
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        return

                    task.set_status("completed")
                    return
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                task.set_status("failed", str(e))
                return
            except Exception as e:
                task.set_status("failed", str(e))
                return

    async def start_downloads(self):
        if self.running:
            return
        self.running = True
        await asyncio.gather(*(self.download_file(task) for task in self.tasks))
        self.running = False

    def cancel_all(self):
        for task in self.tasks:
            task.cancel_event.set()

    def clear_completed(self):
        self.tasks = [t for t in self.tasks if t.status not in ("completed", "failed")]


download_manager = DownloadManager()