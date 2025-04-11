import os
import asyncio
import aiohttp
import aiofiles
import time
import random
from typing import Dict, List, Optional
from settings import load_settings

MAX_RETRIES = 100
CHUNK_TIMEOUT = 60
MAX_CONCURRENT_DOWNLOADS = 10
CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/103.0.0.0 Safari/537.36"
]

def format_size(bytes_size: float) -> str:
    if bytes_size >= 1024 ** 3:
        return f"{bytes_size / 1024 ** 3:.2f} GB"
    elif bytes_size >= 1024 ** 2:
        return f"{bytes_size / 1024 ** 2:.2f} MB"
    elif bytes_size >= 1024:
        return f"{bytes_size / 1024:.2f} KB"
    else:
        return f"{bytes_size:.2f} bytes"

def format_time(seconds: float) -> str:
    if seconds >= 3600:
        return f"{int(seconds // 3600)} hora(s) restantes"
    elif seconds >= 60:
        return f"{int(seconds // 60)} min restantes"
    else:
        return f"{int(seconds)} seg restantes"

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
        self.last_update_time: Optional[float] = None

    def update_progress(self):
        now = time.monotonic()
        if self.start_time is None:
            self.start_time = now
        self.last_update_time = now

        downloaded = os.path.getsize(self.dest_path) if os.path.exists(self.dest_path) else 0
        elapsed = max(1e-6, now - self.start_time)
        speed = downloaded / elapsed
        remaining = max(self.file_size - downloaded, 0)
        eta = remaining / speed if speed > 0 else None

        percent = min(100, int(downloaded * 100 / self.file_size))
        if self.ui_elements.get('progress'):
            self.ui_elements['progress'].value = percent / 100
            self.ui_elements['progress'].props(f'label="{percent}%"')

        if self.ui_elements.get('status'):
            downloaded_str = format_size(downloaded)
            expected = format_size(self.file_size)
            speed_str = format_size(speed) + '/s'
            eta_str = format_time(eta) if eta else "Calculando..."
            status_text = f"{speed_str} — {downloaded_str} de {expected}, {eta_str}"
            self.ui_elements['status'].text = status_text[:70] + '…' if len(status_text) > 70 else status_text

    def set_status(self, status: str, error: str = None):
        self.status = status
        self.error_message = error
        icon = None
        if status == "queued": icon = ('hourglass_empty', 'gray')
        elif status == "downloading": icon = ('cloud_download', 'blue')
        elif status == "completed": icon = ('check_circle', 'green')
        elif status == "failed": icon = ('error', 'red')
        elif status == "cancelled": icon = ('cancel', 'orange')

        if self.ui_elements.get('status_icon') and icon:
            self.ui_elements['status_icon'].props(f"name={icon[0]} color={icon[1]}")

        if self.ui_elements.get('status'):
            if status == "failed" and error:
                self.ui_elements['status'].text = f"{error}"
            elif status == "completed":
                self.ui_elements['status'].text = "Concluído"
            elif status == "cancelled":
                self.ui_elements['status'].text = "Cancelado"

        if status in ("completed", "failed", "cancelled"):
            cancel_btn = self.ui_elements.get('cancel_btn')
            if cancel_btn:
                cancel_btn.set_visibility(False)

class DownloadManager:
    def __init__(self):
        self.tasks: List[DownloadTask] = []
        self.max_concurrent_downloads = MAX_CONCURRENT_DOWNLOADS
        self.semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
        self.running = False

    def add_task(self, url: str, month_key: str, filename: str, file_size: int, force: bool = False) -> DownloadTask:
        settings = load_settings()
        download_path = settings.get("download_path", "")
        month_dir = os.path.join(download_path, month_key)
        os.makedirs(month_dir, exist_ok=True)
        dest_path = os.path.join(month_dir, filename)

        task = DownloadTask(url, dest_path, file_size, month_key, filename)

        if not force and os.path.exists(dest_path) and os.path.getsize(dest_path) == file_size:
            print(f"Arquivo já existe: {filename}, marcando como concluído.")
            task.set_status("completed")
        else:
            self.tasks.append(task)

        return task

    async def download_file(self, task: DownloadTask):
        attempt = 0
        while attempt < MAX_RETRIES:
            if task.cancel_event.is_set():
                task.set_status("cancelled")
                return

            task.set_status("downloading")
            task.start_time = time.monotonic()
            task.last_update_time = task.start_time
            timeout = aiohttp.ClientTimeout(total=300)

            existing_size = os.path.getsize(task.dest_path) if os.path.exists(task.dest_path) else 0

            try:
                async with self.semaphore:
                    headers = {
                        'User-Agent': random.choice(USER_AGENTS),
                        'Range': f'bytes={existing_size}-'
                    }
                    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                        async with session.get(task.url) as response:
                            if response.status not in (200, 206):
                                raise aiohttp.ClientError(f"HTTP {response.status}")

                            content_type = response.headers.get('Content-Type', '')
                            if 'application/zip' not in content_type:
                                raise aiohttp.ClientError(f"Tipo de conteúdo inesperado: {content_type}")

                            content_length = response.headers.get('Content-Length')
                            if content_length and content_length.isdigit():
                                task.file_size = existing_size + int(content_length)

                            mode = 'ab' if existing_size > 0 else 'wb'
                            async with aiofiles.open(task.dest_path, mode) as f: # type: ignore
                                first_chunk = True
                                while True:
                                    if task.cancel_event.is_set():
                                        break
                                    chunk = await asyncio.wait_for(
                                        response.content.read(CHUNK_SIZE),
                                        timeout=CHUNK_TIMEOUT
                                    )
                                    if not chunk:
                                        break
                                    if first_chunk and existing_size == 0 and not chunk.startswith(b'PK'):
                                        raise aiohttp.ClientError("Conteúdo não parece ser um ZIP válido")
                                    first_chunk = False
                                    await f.write(chunk) # type: ignore
                                    task.update_progress()

                if task.cancel_event.is_set():
                    task.set_status("cancelled")
                    await asyncio.sleep(0.1)
                    if os.path.exists(task.dest_path):
                        os.remove(task.dest_path)
                    return

                task.set_status("completed")
                return

            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                attempt += 1
                if attempt < MAX_RETRIES:
                    task.set_status("downloading")
                    if task.ui_elements.get('status'):
                        task.ui_elements['status'].text = f"Tentativa {attempt + 1} de {MAX_RETRIES}..."
                    await asyncio.sleep(random.uniform(1.5, 3.5))
                    continue
                task.set_status("failed", f"Falhou")
                return

            except Exception as e:
                task.set_status("failed", f"Erro: {str(e)}")
                return

    async def start_downloads(self):
        if self.running:
            return
        self.running = True
        await asyncio.gather(*(self.download_file(task) for task in self.tasks if task.status in ('queued', 'downloading')))
        self.running = False

    def cancel_all(self):
        for task in self.tasks:
            if task.status in ('queued', 'downloading'):
                task.cancel_event.set()
                task.set_status("cancelled")
                if os.path.exists(task.dest_path):
                    try:
                        os.remove(task.dest_path)
                    except Exception as e:
                        print(f"Erro ao remover arquivo cancelado: {e}")

    def clear_completed(self):
        self.tasks = [t for t in self.tasks if t.status not in ("completed", "failed")]

download_manager = DownloadManager()
