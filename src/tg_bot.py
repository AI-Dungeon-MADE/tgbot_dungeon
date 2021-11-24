import random
import uuid
from typing import Dict, Tuple, List

from loguru import logger
from made_ai_dungeon import StoryManager
from made_ai_dungeon.models.generator_stub import GeneratorStub
from made_ai_dungeon.models.rest_api_generator import RestApiGenerator
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from src.entities import RestGenerators, read_rest_generators_config
from src.game_logs import LogWriter
from src.helpers import get_keyboard
from src.message_processing import process_message

UNKNOWN_SESSION = "unknown session"


# Define a few command handlers. These usually take the two arguments update and
# context.


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
        input_message = "\n>Вы " + update.message.text
        logger.debug("Chat ID: {uid}, Input message: {im}", uid=chat_id, im=input_message)
        picked_sm = self.picked_story_manager.get(chat_id, "default")
        logger.debug("picked story manager {psm}", psm=picked_sm)
        story_uid = self.cur_story_uid.get((chat_id, picked_sm))
        if story_uid is None:
            keyboard = [[InlineKeyboardButton("Начать игру", callback_data="get_stories")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("Для начала игры нажми сюда", reply_markup=reply_markup)
        else:
            reply_message = self.story_managers[picked_sm].generate_story(chat_id, input_message)
            logger.debug(f"{reply_message=}")
            processed_reply_message = process_message(reply_message)
            self.log_writer.write(
                chat_id,
                story_uid,
                picked_sm,
                "user",
                input_message
            )
            self.log_writer.write(
                chat_id,
                story_uid,
                picked_sm,
                "bot",
                processed_reply_message
            )
            keyboard = [[InlineKeyboardButton("Закончить игру", callback_data="end_story")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(processed_reply_message, reply_markup=reply_markup)

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

    def select_generator_callback(self, update, context: CallbackContext) -> None:
        chat_id = update.callback_query.message.chat_id
        picked_sm = update.callback_query.data[17:]
        self.picked_story_manager[chat_id] = picked_sm
        keyboard = [[InlineKeyboardButton("Начать игру", callback_data="get_stories")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.reply_text(f"Генератор: {picked_sm}", reply_markup=reply_markup)

    def reset_context(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        for sm in self.story_managers.values():
            if chat_id in sm.story_context_cache:
                sm.story_context_cache.pop(chat_id)
        update.message.reply_text(
            "Вам понравилось? \n Пожалуйста, заполните форму с вашими впечатлениями об игре, это поможет нам стать лучше. Спасибо!\nhttps://ru.surveymonkey.com/r/63HC7NV ")

    def start_story_command(self, update: Update, context: CallbackContext) -> None:
        story_name = None
        if len(context.args) != 0:
            story_name = context.args[0]
        self.start_story_process(update, story_name)

    def start_story_callback(self, update: Update, context: CallbackContext) -> None:
        logger.debug("Start story debug {d}", d=update.callback_query.data)
        story_name = update.callback_query.data[12:]
        self.start_story_process(update.callback_query, story_name)

    def start_story_process(self, update: Update, story_name: str) -> None:
        start_text_lts = self.story_starts.get(story_name)
        if start_text_lts is None:
            random_key = random.choice(list(self.story_starts.keys()))
            update.message.reply_text(f"Автоматически выбранная тема игры: {random_key}")
            start_text_lts = self.story_starts[random_key]
        start_text = random.choice(start_text_lts)
        chat_id = update.message.chat_id
        logger.info("Chat ID {ci} started new story", ci=chat_id)
        picked_sm = self.picked_story_manager.get(chat_id, "default")
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
        if update.callback_query is not None:
            update = update.callback_query
        start_help = "Я бот для игры AI DUNGEON на русском языке. (Выпускной проект в MADE VK)."
        story_start_help = "\nДля начала игры нажмите Начать игру"
        generator_help = "\nДля выбора генератора текста нажмите на Выбрать генератор"
        help_message = start_help + story_start_help + generator_help
        keyboard = [
            [
                InlineKeyboardButton("Начать игру", callback_data="get_stories"),
                InlineKeyboardButton("Выбор генератора", callback_data="get_generators"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(help_message, reply_markup=reply_markup)

    def start(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        logger.info("/start done")
        keyboard = [
            [
                InlineKeyboardButton("Help", callback_data="help"),
                InlineKeyboardButton("Начать игру", callback_data="get_stories")
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f'Привет {user.full_name}!\nДоброе пожаловать в AI DUNGEON на русском',
            reply_markup=reply_markup,
        )

    def get_stories(self, update: Update, context: CallbackContext) -> None:
        keyboard = get_keyboard(list(self.story_starts.keys()), "start_story")
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.reply_text(
            "Выберите тему, чтобы начать свою историю",
            reply_markup=reply_markup,
        )

    def get_generators(self, update: Update, context: CallbackContext) -> None:
        keyboard = get_keyboard(list(self.story_managers.keys()), "select_generator")
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.reply_text(
            "Выбор генератора",
            reply_markup=reply_markup,
        )

    def end_story(self, update: Update, context: CallbackContext) -> None:
        keyboard = [[InlineKeyboardButton(str(i), callback_data=f"game_score {i}") for i in range(1, 6)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.reply_text(
            "Оцените игру по 5-и бальной шкале. Также Вы можете оставить более полный отзыв заполнив опросник, "
            "это поможет на стать лучше.\nhttps://ru.surveymonkey.com/r/63HC7NV",
            reply_markup=reply_markup,
        )

    def log_game_score(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.callback_query.message.chat_id
        picked_sm = self.picked_story_manager.get(chat_id, "default")
        story_uid = self.cur_story_uid.get((chat_id, picked_sm), UNKNOWN_SESSION)
        self.log_writer.write(
            chat_id,
            story_uid,
            picked_sm,
            "game_score",
            update.callback_query.data[11:],
        )
        keyboard = [[InlineKeyboardButton("Начать новую игру", callback_data="get_stories")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.reply_text("Спасибо!\nДля начала новой игры нажми сюда",
                                                 reply_markup=reply_markup)
