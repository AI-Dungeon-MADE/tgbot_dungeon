import os
from typing import Dict, List

import torch
from loguru import logger
from made_ai_dungeon import StoryManager
from made_ai_dungeon.models import HugginfaceGenerator
from made_ai_dungeon.models.generator_stub import GeneratorStub
from made_ai_dungeon.models.rest_api_generator import RestApiGenerator
from telegram import Update
from telegram.ext import CallbackContext

from src.lstm import CharLSTM
from src.message_processing import process_message


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info("/start done")
    update.message.reply_text(
        fr'Hi {user.mention_markdown_v2()}\!',
    )  # reply_markdown_v2


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        """Select story generator:\n 0 - Stub, \n 1 - LSTM, \n 2 - Hugginface Generator \n 
        3 - RestApi Generator (Example: /set_generator 0)"""
    )


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


class GameManager:

    def __init__(self) -> None:
        model = CharLSTM(num_layers=2, num_units=196, dropout=0.05)
        model.load_state_dict(torch.load('/app/models/Char_LSTM_Samurai.pth'))
        logger.info("Successfully loaded model weights")
        hug_api_url = "https://api-inference.huggingface.co/models/Mary222/MADE_AI_Dungeon_model_RUS"
        collab_url = os.environ["COLLAB_HOST"]
        headers = {"Authorization": os.environ["HUGGINFACE_KEY"]}
        self.story_managers: List[StoryManager] = [
            StoryManager(GeneratorStub()),
            StoryManager(model),
            StoryManager(HugginfaceGenerator(hug_api_url, headers)),
            StoryManager(RestApiGenerator(collab_url, 2000)),
        ]
        self.picked_story_manager: Dict[int, int] = {}

    def reply(self, update: Update, context: CallbackContext) -> None:
        """Echo the user message."""
        chat_id = update.message.chat_id
        input_message = "Вы сказали: " + update.message.text
        logger.debug("Chat ID: {uid}, Input message: {im}", uid=chat_id, im=input_message)
        picked_sm = self.picked_story_manager.get(chat_id, 0)
        logger.debug("picked story manager {psm}", psm=picked_sm)
        reply_message = self.story_managers[picked_sm].generate_story(chat_id, input_message)
        logger.debug(f"{reply_message=}")
        processed_reply_message = process_message(reply_message)
        update.message.reply_text(processed_reply_message)

    def select_generator(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        try:
            logger.info(context)
            picked_story = int(context.args[0])
            if picked_story in set(range(len(self.story_managers))):
                self.picked_story_manager[chat_id] = int(context.args[0])
                update.message.reply_text(f"Chat ID {chat_id} picked generator is {picked_story}")
            else:
                update.message.reply_text("Usage: /set_generator <0, 1, 2, 3>")
        except (IndexError, ValueError):
            update.message.reply_text("Usage: /set_generator <0, 1, 2, 3>")

    def reset_context(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        for sm in self.story_managers:
            if chat_id in sm.story_context_cache:
                sm.story_context_cache.pop(chat_id)

    def start_story(self, update: Update, context: CallbackContext) -> None:
        start_text = """Ты - Юлий Цезарь, консул Рима. Вы сражаетесь с галлами к северу от Римской республики, чтобы победить 
        варварские племена, которые угрожают вашей великой нации. Вы входите в военный штаб и 
        видите сегодняшний военный брифинг."""
        chat_id = update.message.chat_id
        logger.info("Chat ID {ci} started new story", ci=chat_id)
        picked_sm = self.picked_story_manager.get(chat_id, 0)
        story_manager = self.story_managers[picked_sm]
        if chat_id in story_manager.story_context_cache:
            story_manager.story_context_cache.pop(chat_id)
        reply_message = story_manager.generate_story(chat_id, start_text)
        update.message.reply_text(reply_message)
