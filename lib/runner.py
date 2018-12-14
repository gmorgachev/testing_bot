import logging
import logging.handlers
from telegram.ext import Updater


class TelegramBotLogHandler(logging.handlers.BufferingHandler):
    def __init__(self, bot, chat_id, capacity):
        logging.handlers.BufferingHandler.__init__(self, 1)
        self.chat_id = chat_id
        self.bot = bot
        self.setFormatter(TestingBotRunner.log_formatter)

    def flush(self):
        if self.buffer:
            try:
                msg = ""
                for record in self.buffer:
                    s = self.format(record)
                    msg = msg + s + "\r\n"
                self.bot.send_message(chat_id=self.chat_id, text=msg)
            except Exception:
                self.handleError(None)
            super(TelegramBotLogHandler, self).flush()


class TestingBotRunner:
    # Formatter for logger
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    @staticmethod
    def run(testing, name, token, request_kwargs, chat_id):
        updater = Updater(token=token, request_kwargs=request_kwargs)

        logger = TestingBotRunner.setup_logger(
            "tmp_{0}".format(name), "tmp_{0}.log".format(name))
        logger.info("Init log")
        handler = TelegramBotLogHandler(updater.bot, chat_id, 10)
        handler.setFormatter(TestingBotRunner.log_formatter)
        logger.addHandler(handler)
        
        try:
            testing.run(logger=logger)
        except Exception as e:
            logger.exception(e)
        finally:
            updater.stop()

    @staticmethod
    def setup_logger(name, log_file, level=logging.INFO):
        handler = logging.FileHandler(log_file)        
        handler.setFormatter(TestingBotRunner.log_formatter)

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)

        return logger