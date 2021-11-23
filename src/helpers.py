import json
from typing import Dict, List

from telegram import InlineKeyboardButton


def load_prompts(path: str) -> Dict[str, List[str]]:
    with open(path) as json_file:
        data = json.load(json_file)
    return data


def get_story_keyboard(story_list: List[str]) -> List[InlineKeyboardButton]:
    keyboard = []
    for story_name in story_list:
        keyboard.append([
            InlineKeyboardButton(story_name, callback_data=f"start_story {story_name}"),
        ])
    return keyboard
