import csv
import time


class LogWriter:
    def __init__(self, filename) -> None:
        self.filename = filename

    def write(self, chat_id: int, session_uid: str, instance: str, source: str, text: str) -> None:
        now = int(time.time())
        row_lst = [str(chat_id), session_uid, instance, source, text, str(now)]
        with open(self.filename, "a") as csv_file:
            writer = csv.writer(csv_file, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(row_lst)
