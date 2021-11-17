import json
from typing import Dict, List


def load_prompts(path: str) -> Dict[str, List[str]]:
    with open(path) as json_file:
        data = json.load(json_file)
    return data
