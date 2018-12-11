import sys
import telegram
import logging
import string, logging
import threading
import json
import time

from time import sleep
from telegram.ext import Updater, Dispatcher
from telegram.ext import MessageHandler, Filters
from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import utils

# Import test project
# Bad way
# TODO: to do package setup for NNCA
sys.path.insert(0, "../CSharpCodeChecker/")
from NNCA.lib.model import Model


with open("./config.json", "r") as f:
    cfg = json.load(f)

# Formatter for logger
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

def setup_logger(name, log_file, level=logging.INFO):
    
    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

class TelegramBotHandler(logging.handlers.BufferingHandler):
    def __init__(self, bot, chat_id, capacity):
        logging.handlers.BufferingHandler.__init__(self, 1)
        self.chat_id = chat_id
        self.bot = bot
        self.setFormatter(formatter)

    def flush(self):
        if len(self.buffer) > 0:
            try:
                msg = ""
                for record in self.buffer:
                    s = self.format(record)
                    msg = msg + s + "\r\n"
                self.bot.send_message(chat_id=self.chat_id, text=msg)
            except:
                self.handleError(None)
            super(TelegramBotHandler, self).flush()

            
class TestingBot:
    def __init__(self, cfg):
        self.default_params = cfg["params"]
        self.my_chat_id = cfg["chat_id"]
        self.bot = telegram.Bot(token=cfg["token"], )
        self.updater = Updater(token=cfg["token"], request_kwargs=cfg["request_kwargs"])
        self.dispatcher = self.updater.dispatcher

        self.dispatcher.add_handler(CommandHandler('start', self.start, pass_user_data=True))
        self.dispatcher.add_handler(CommandHandler('run', self.run_function, pass_user_data=True, pass_args=True))
        self.dispatcher.add_handler(CommandHandler('params', self.params_function, pass_user_data=True))
        # self.dispatcher.add_handler(CommandHandler('stop', self.stop, pass_user_data=True))
        self.dispatcher.add_handler(MessageHandler(Filters.text, self.text_handler, pass_user_data=True))
        self.dispatcher.add_handler(CallbackQueryHandler(self.button, pass_user_data=True))

        self.logger = setup_logger('first_logger', 'logfile.log')
        self.logger.info('Init log')
        handler = TelegramBotHandler(self.updater.bot, self.my_chat_id, 10)
        # handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def start_pooling(self):
        self.updater.start_polling()

    @staticmethod
    def foo(params, logger, train_args):
        try:
            model = Model(params=params, logger=logger)
            valid = model.train(*[int(arg) for arg in train_args])

            return model
        except:
            logging.error("Model creation error")
            raise

    def start(self, bot, update, user_data):
        bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me")
        user_data["params"] = dict()
        user_data["wait_for"] = None
        for key in self.default_params:
            user_data["params"][key] = self.default_params[key]

    def params_function(self, bot, update, user_data):
        button_list = []
        for key in user_data["params"]:
            button_list.append(InlineKeyboardButton(key + " " + str(user_data["params"][key]), callback_data=key))
        reply_markup = InlineKeyboardMarkup(self.build_menu(button_list, n_cols=2))     
        bot.send_message(chat_id=update.message.chat_id, text="Choose parameter", reply_markup=reply_markup)

    def run_function(self, bot, update, user_data, args):
        try:
            t1 = threading.Thread(target=TestingBot.foo, args=(user_data["params"], self.logger, args))
            user_data["model_thread"] = t1
            t1.start()
        except:
            logging.error("HZ")

            raise

    # def stop(self, bot, update, user_data):
    #     try:
    #         user_data["model_thread"].stop()
    #         user_data["model_thread"].join()
    #     except KeyError:
    #         self.logger.warning("Key error")
    #         raise
    #     except:
    #         self.logger.error("Something strange in stop")
    #         raise
        
    def text_handler(self, bot, update, user_data):
        try:
            wait_for = user_data["wait_for"]
            if wait_for not in user_data["params"]:
                raise KeyError
            user_data["params"][wait_for] = type(user_data["params"][wait_for])(update.message.text)
            update.message.reply_text(text="New {0} is {1}".format(wait_for, user_data["params"][wait_for]))

        except KeyError:
            update.message.reply_text('Not found')


    def button(self, bot, update, user_data):
        query = update.callback_query
        user_data["wait_for"] = query.data
        bot.edit_message_text(text="Wait for {0}".format(query.data), 
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)

    def build_menu(self, buttons, n_cols, header_buttons=None, footer_buttons=None):
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
        if header_buttons:
            menu.insert(0, header_buttons)
        if footer_buttons:
            menu.append(footer_buttons)
        return menu