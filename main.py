import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from src.helpers import load_prompts
from src.tg_bot import start, GameManager


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(os.environ["TOKEN"])
    config_path = "app/config/rest_generator_config.yaml"
    game_logs_file = "app/game_logs.csv"
    start_story_dict = load_prompts("app/data/prompts.json")
    game_manager = GameManager(config_path, game_logs_file, start_story_dict)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", game_manager.help_command))
    dispatcher.add_handler(CommandHandler("set_generator", game_manager.select_generator))
    dispatcher.add_handler(CommandHandler("reset", game_manager.reset_context))
    dispatcher.add_handler(CommandHandler("start_story", game_manager.start_story))
    dispatcher.add_handler(CommandHandler("update_generators", game_manager.update_generators))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, game_manager.reply))

    # Start the Bot
    updater.start_polling(timeout=1000, drop_pending_updates=True)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
