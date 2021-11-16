import uuid
from typing import Dict, Tuple, List

from loguru import logger
from made_ai_dungeon import StoryManager
from made_ai_dungeon.models.generator_stub import GeneratorStub
from made_ai_dungeon.models.rest_api_generator import RestApiGenerator
from telegram import Update
from telegram.ext import CallbackContext

from src.entities import RestGenerators, read_rest_generators_config
from src.game_logs import LogWriter
from src.message_processing import process_message

UNKNOWN_SESSION = "unknown session"


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info("/start done")
    update.message.reply_text(
        fr'Hi {user.mention_markdown_v2()}\! \nДля получения информации введите /help',
    )  # reply_markdown_v2


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


class GameManager:

    def __init__(
            self, generator_config_path: str,
            logs_file: str,
            story_starts: Dict[str, List[str]],
    ) -> None:
        self.story_managers: Dict[StoryManager] = {"stub": StoryManager(GeneratorStub())}
        self.generator_config_path = generator_config_path
        rest_generators_configs: RestGenerators = read_rest_generators_config(self.generator_config_path)
        url_generators = {name: StoryManager(RestApiGenerator(host_url=url, context_length=5000))
                          for name, url in rest_generators_configs.generators.items()}
        self.story_managers.update(url_generators)
        self.picked_story_manager: Dict[int, str] = {}
        self.cur_story_uid: Dict[Tuple[int, str], str] = {}
        self.log_writer = LogWriter(logs_file)
        self.story_starts = story_starts

    def reply(self, update: Update, context: CallbackContext) -> None:
        """Echo the user message."""
        chat_id = update.message.chat_id
        input_message = "\n" + update.message.text
        logger.debug("Chat ID: {uid}, Input message: {im}", uid=chat_id, im=input_message)
        picked_sm = self.picked_story_manager.get(chat_id, "stub")
        logger.debug("picked story manager {psm}", psm=picked_sm)
        reply_message = self.story_managers[picked_sm].generate_story(chat_id, input_message)
        logger.debug(f"{reply_message=}")
        processed_reply_message = process_message(reply_message)
        self.log_writer.write(
            chat_id,
            self.cur_story_uid.get((chat_id, picked_sm), UNKNOWN_SESSION),
            picked_sm,
            "user",
            input_message
        )
        self.log_writer.write(
            chat_id,
            self.cur_story_uid.get((chat_id, picked_sm), UNKNOWN_SESSION),
            picked_sm,
            "bot",
            processed_reply_message
        )
        update.message.reply_text(processed_reply_message)

    def select_generator(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        generators_str = ' '.join(self.story_managers.keys())
        try:
            logger.info(context)
            picked_story = context.args[0]
            if picked_story in self.story_managers.keys():
                self.picked_story_manager[chat_id] = picked_story
                update.message.reply_text(f"Chat ID {chat_id} picked generator is {picked_story}")
            else:
                update.message.reply_text(f"Usage: /set_generator <{generators_str}>")
        except (IndexError, ValueError):
            update.message.reply_text(f"Usage: /set_generator <{generators_str}>")

    def reset_context(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        for sm in self.story_managers:
            if chat_id in sm.story_context_cache:
                sm.story_context_cache.pop(chat_id)

    def start_story(self, update: Update, context: CallbackContext) -> None:
        start_text = self.story_starts.get(context.args[0])
        if start_text is None:
            story_starts_str = '\n'.join(self.story_starts.keys())
            story_help = f"""\nДля начала игры нажмите /start_story <тема приключений>
            Список тем:
            \n{story_starts_str}\n (Example /start_story cesar)"""
            update.message.reply_text(story_help)
        else:
            chat_id = update.message.chat_id
            logger.info("Chat ID {ci} started new story", ci=chat_id)
            picked_sm = self.picked_story_manager.get(chat_id, "stub")
            story_manager = self.story_managers[picked_sm]
            if chat_id in story_manager.story_context_cache:
                story_manager.story_context_cache.pop(chat_id)
            self.cur_story_uid[(chat_id, picked_sm)] = str(uuid.uuid4())
            reply_message = start_text + story_manager.generate_story(chat_id, start_text)
            self.log_writer.write(
                chat_id,
                self.cur_story_uid.get((chat_id, picked_sm), UNKNOWN_SESSION),
                picked_sm,
                "bot",
                reply_message
            )
            update.message.reply_text(reply_message)

    def update_generators(self, update: Update, context: CallbackContext) -> None:
        rest_generators_configs: RestGenerators = read_rest_generators_config(self.generator_config_path)
        pop_set = set(self.story_managers.keys()) - set(rest_generators_configs.generators.keys())
        pop_set -= {"stub"}
        for name in pop_set:
            self.story_managers.pop(name)
        for name, url in rest_generators_configs.generators.items():
            self.story_managers[name] = StoryManager(RestApiGenerator(host_url=url,
                                                                      context_length=5000))
        update.message.reply_text("Generators updated")

    def help_command(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /help is issued."""
        generators_str = '\n'.join(self.story_managers.keys())
        story_starts_str = '\n'.join(self.story_starts.keys())
        generators_help = f"\nДля начала игры выберите генератор историй (по умолчанию будете получать эхо :smile: ):\n{generators_str} \n(Example: /set_generator stub)"
        start_help = "Я бот для игры AI DUNGEON на русском языке. (Выпускной проект в MADE VK)."
        story_help = f"\nДля начала игры нажмите /start_story <тема приключений> \n{story_starts_str}\n (Example /start_story cesar)"
        help_message = start_help + generators_help + story_help
        update.message.reply_text(help_message)
