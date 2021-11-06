import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from src.tg_bot import start, help_command, GameManager


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(os.environ["TOKEN"])
    game_manager = GameManager()

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("set_generator", game_manager.select_generator))
    dispatcher.add_handler(CommandHandler("reset", game_manager.reset_context))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, game_manager.reply))

    # Start the Bot
    updater.start_polling(timeout=100) # drop_pending_updates=True

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
