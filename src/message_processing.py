import re


def process_message(raw_text: str) -> str:
    filtered_text = re.sub("\s+", "", raw_text)
    if len(filtered_text) == 0:
        return "Сгенерировано пустое сообщение, попробуйте дополнить свой запрос"
    return raw_text
