import platform
import os
import ctypes
from pathlib import Path
from typing import Optional, Any, List
from nicegui import events, ui

# Define constants for Windows file attributes
FILE_ATTRIBUTE_HIDDEN = 2

# Try to import win32api for Windows, but provide fallbacks if not available
try:
    import win32api
    import win32con

    HAS_WIN32API = True
except ImportError:
    HAS_WIN32API = False
    win32api = None  # type: Any


class LocalFolderPicker(ui.dialog):
    """A dialog for picking folders from the local filesystem."""

    def __init__(self, directory: str, *,
                 upper_limit: Optional[str] = ..., show_hidden_folders: bool = False) -> None:
        """Local Folder Picker

        This is a simple folder picker that allows you to select a folder from the local filesystem where NiceGUI is running.

        :param directory: The directory to start in.
        :param upper_limit: The directory to stop at (None: no limit, default: same as the starting directory).
        :param show_hidden_folders: Whether to show hidden folders (default: False).
        """
        super().__init__()
        self.path = Path(directory).expanduser()
        self.drives_toggle = None  # Define attribute in __init__

        if upper_limit is None:
            self.upper_limit = None
        else:
            self.upper_limit = Path(directory if upper_limit is ... else upper_limit).expanduser()
        self.show_hidden_folders = show_hidden_folders

        with self, ui.card():
            ui.label('Selecione a pasta').classes('text-lg font-bold')
            self.current_path_label = ui.label(f'Pasta atual: {self.path}').classes('text-sm text-gray-500 outlined')
            self.add_drives_toggle()
            self.grid = ui.aggrid({
                'columnDefs': [{'field': 'name', 'headerName': 'Pasta'}],
                'rowSelection': 'single',
            }, html_columns=[0]).classes('w-96').on('cellDoubleClicked', self.handle_double_click)
            with ui.row().classes('w-full justify-end'):
                ui.button('Cancelar', on_click=self.close, color="negative").props('outline')
                ui.button('Confirmar', on_click=self._select_current_folder)
        self.update_grid()

    @staticmethod
    def get_windows_drives() -> List[str]:
        """Get a list of available drives on Windows.

        Returns:
            List[str]: List of drive paths
        """
        if not platform.system() == 'Windows':
            return []

        drives = []

        # Try using win32api if available
        if HAS_WIN32API:
            try:
                get_drives_func = getattr(win32api, 'GetLogicalDriveStrings', None)
                if get_drives_func:
                    drives = get_drives_func().split('\000')[:-1]
            except (AttributeError, OSError):
                # win32api available but function failed
                pass

        # Fallback method if win32api failed or is not available
        if not drives:
            drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:")]

        return drives

    def add_drives_toggle(self) -> None:
        """Add a toggle for selecting drives on Windows platforms."""
        if platform.system() == 'Windows':
            drives = self.get_windows_drives()

            if drives:
                with ui.row().classes('w-full items-center'):
                    ui.label('Drive:')
                    self.drives_toggle = ui.toggle(drives, value=drives[0], on_change=self.update_drive)

    def update_drive(self) -> None:
        """Update the current path when a drive is selected."""
        if self.drives_toggle is not None:
            self.path = Path(self.drives_toggle.value).expanduser()
            self.update_grid()

    @staticmethod
    def is_hidden(path: Path) -> bool:
        """Check if a path is hidden.

        Args:
            path: The path to check

        Returns:
            bool: True if the path is hidden, False otherwise
        """
        # Check for dot-prefixed hidden files (Unix style)
        if path.name.startswith('.'):
            return True

        # Check for Windows hidden attribute
        if platform.system() == 'Windows':
            if HAS_WIN32API:
                try:
                    get_attrs_func = getattr(win32api, 'GetFileAttributes', None)
                    if get_attrs_func:
                        attrs = get_attrs_func(str(path))
                        return bool(attrs & FILE_ATTRIBUTE_HIDDEN)
                except (AttributeError, OSError):
                    pass

            # Fallback using ctypes if win32api failed or is not available
            try:
                return bool(ctypes.windll.kernel32.GetFileAttributesW(str(path)) & FILE_ATTRIBUTE_HIDDEN)
            except (AttributeError, OSError):
                pass

        return False

    def update_grid(self) -> None:
        """Update the grid with the current directory contents."""
        self.current_path_label.text = f'Caminho atual: {self.path}'

        try:
            paths = list(self.path.glob('*'))

            # Filter to only include directories
            paths = [p for p in paths if p.is_dir()]

            # Filter out hidden folders
            if not self.show_hidden_folders:
                paths = [p for p in paths if not self.is_hidden(p)]

            paths.sort(key=lambda p: p.name.lower())

            self.grid.options['rowData'] = [
                {
                    'name': f'📁 <strong>{p.name}</strong>',
                    'path': str(p),
                }
                for p in paths
            ]

            if (self.upper_limit is None and self.path != self.path.parent) or \
                    (self.upper_limit is not None and self.path != self.upper_limit):
                self.grid.options['rowData'].insert(0, {
                    'name': f'📁 <strong>..</strong>',
                    'path': str(self.path.parent),
                })

            self.grid.update()
        except PermissionError:
            ui.notify('Permission denied to access this directory', type='negative')
            # Try to go back to parent directory
            self.path = self.path.parent
            self.update_grid()
        except OSError as e:
            ui.notify(f'Error accessing directory: {str(e)}', type='negative')
            # Try to go back to parent directory
            self.path = self.path.parent
            self.update_grid()

    def handle_double_click(self, e: events.GenericEventArguments) -> None:
        """Handle double-click on a folder in the grid."""
        self.path = Path(e.args['data']['path'])
        self.update_grid()

    def _select_current_folder(self) -> None:
        """Select the current folder and close the dialog."""
        self.submit(str(self.path))