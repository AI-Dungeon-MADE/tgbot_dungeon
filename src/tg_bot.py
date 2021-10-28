from loguru import logger
from made_ai_dungeon import StoryManager
from made_ai_dungeon.models.generator_stub import GeneratorStub
from telegram import Update, ForceReply
from telegram.ext import CallbackContext


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info("/start done")
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


class GameManager:

    def __init__(self) -> None:
        self.story_manager = StoryManager(GeneratorStub())

    def reply(self, update: Update, context: CallbackContext) -> None:
        """Echo the user message."""
        user_id = str(update.chat_member.from_user.id)
        input_message = update.message.text
        logger.debug("User ID: {uid}, Input message: {im}", uid=user_id, im=input_message)
        reply_message = self.story_manager.generate_story(user_id, input_message)
        reply_message += user_id
        update.message.reply_text(reply_message)
