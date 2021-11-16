import csv
from src.game_logs import LogWriter


def test_log_writer() -> None:
    log_writer = LogWriter("test_logs.csv")
    log_writer.write(3, "session", "source", "instance", "message")
    log_writer.write(3, "session", "source", "instance", "message")
    with open("test_logs.csv", "r") as csv_file:
        reader = csv.reader(csv_file, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        cnt = 0
        for _ in reader:
            cnt += 1
    assert cnt >= 2
