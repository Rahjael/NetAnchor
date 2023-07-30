from datetime import datetime
import json
import time

class Logger:
    def __init__(self):
        self.logs = []

    def log(self, *args):
        message = ' '.join(str(arg) if not isinstance(arg, dict) else json.dumps(arg) for arg in args)
        date = datetime.now()
        time.sleep(1/10)
        self.logs.append((date, message))
        self.logs.sort(reverse=True)
        print('LOGGER: ', message)

    def get_logs_as_strings(self) -> list[str]:
        return [f"{log[0].strftime('%Y-%m-%d %H:%M:%S')} - {log[1]}" for log in self.logs]