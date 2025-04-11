from datetime import datetime

class Logger:
    def __init__(self, file_path):
        self.file = open(file_path, 'w', encoding='utf-8')

    def write(self, message):
        trimmed = message.strip()
        if trimmed:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.file.write(f"[{timestamp}] {trimmed}\n")
            self.file.flush()

    def flush(self):
        self.file.flush()
