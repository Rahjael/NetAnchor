from datetime import datetime

class Logger:
    def __init__(self):
        self.logs = []

    def log(self, message: str):
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.logs.append((date, message))
        self.logs.sort(reverse=True)
        print(message)

    def get_logs_as_strings(self) -> list[str]:
        return [f'{log[0]} - {log[1]}' for log in self.logs]