import sys
import inspect
import telegram
import logging
import threading
import json
import time
import lib.candidates

from time import sleep
from telegram.ext import Updater, Dispatcher
from telegram.ext import MessageHandler, Filters
from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import utils
from multiprocessing import Process

from . runner import TestingBotRunner, TelegramBotLogHandler

class TestingBot:
    # Formatter for base_logger
    log_formatter = logging.Formatter('BASE: %(asctime)s %(levelname)s %(message)s')

    def __init__(self, cfg):
        try:
            self.my_chat_id = cfg["chat_id"]
            self.request_kwargs = cfg["request_kwargs"]
            self.remote_device = cfg["remote_device"]

            self.updater = Updater(token=cfg["token"], request_kwargs=self.request_kwargs)
            self.bot = self.updater.bot
            self.dispatcher = self.updater.dispatcher
            self.testing_functions = {}

            self.dispatcher.add_handler(CommandHandler('start', self.start, pass_user_data=True))
            self.dispatcher.add_handler(CommandHandler('run', self.run_function, pass_user_data=True))
            self.dispatcher.add_handler(CommandHandler('remote_run', self.remote_run, pass_user_data=True))
            self.dispatcher.add_handler(CommandHandler('params', self.params_function, pass_user_data=True))
            self.dispatcher.add_handler(CommandHandler('stop', self.stop, pass_user_data=True))
            self.dispatcher.add_handler(CommandHandler('choose', self.choose_project, pass_user_data=True))
            self.dispatcher.add_handler(MessageHandler(Filters.text, self.text_handler, pass_user_data=True))
            self.dispatcher.add_handler(CallbackQueryHandler(self.button, pass_user_data=True))

            self.logger = TestingBotRunner.setup_logger("base_logger", "base_logger.log")
            self.logger.info("Init log")
            handler = TelegramBotLogHandler(self.updater.bot, self.my_chat_id, 10)
            handler.setFormatter(TestingBot.log_formatter)
            self.logger.addHandler(handler)

            for name, obj in inspect.getmembers(sys.modules[lib.candidates.__name__]):
                if inspect.isclass(obj) and issubclass(obj, lib.candidates.TestingBase):
                    self.testing_functions[name] = obj

        except Exception as e:
            self.logger.exception(e)

    def start_pooling(self):
        self.updater.start_polling()

    def start(self, bot, update, user_data):
        try:
            bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me")
            user_data["wait_for"] = None
            user_data["testing_f"] = None
            user_data["testing_functions"] = {}

            for key in self.testing_functions:
                user_data["testing_functions"][key] = self.testing_functions[key]()

        except Exception as e:
            self.logger.exception(e)

    def params_function(self, bot, update, user_data, choosing_params_dict=None):
        try:
            test_function = user_data["testing_f"]
            if choosing_params_dict is None:
                choosing_params_dict = user_data["testing_functions"][test_function].args
            if test_function is None:
                update.reply_text("test_s is none")
                raise KeyError
            button_list = []
            for key in choosing_params_dict:
                button_list.append(
                    InlineKeyboardButton(key + " " + str(choosing_params_dict[key]), callback_data=key))
            reply_markup = InlineKeyboardMarkup(self.build_menu(button_list, n_cols=2))     
            bot.send_message(chat_id=update.message.chat_id, text="Choose parameter", reply_markup=reply_markup)
        except KeyError:
            self.logger.warning("Choosing params error")

    def choose_project(self, bot, update, user_data):
        try:
            project_list = []
            for key in self.testing_functions:
                project_list.append(InlineKeyboardButton(str(key), callback_data=str(key)))

            reply_markup = InlineKeyboardMarkup(self.build_menu(project_list, n_cols=2))
            bot.send_message(chat_id=update.message.chat_id, text="Choose project", reply_markup=reply_markup)

        except Exception as e:
            self.logger.exception(e)

    def run_function(self, bot, update, user_data):
        user_data["model_thread"] = Process(
            target=TestingBotRunner.run,
            args=(user_data["testing_functions"][user_data["testing_f"]],
                "test", self.bot.token, self.request_kwargs, update.message.chat_id)
        )

        user_data["model_thread"].start()
        update.message.reply_text(text="Started")

    def remote_run(self, bot, update, user_data):
        TestingBotRunner.send_remote_task(user_data["testing_functions"][user_data["testing_f"]],
            "test", self.bot.token, self.request_kwargs, update.message.chat_id, self.remote_device)
        update.message.reply_text(text="Started")

    def stop(self, bot, update, user_data):
        try:
            user_data["model_thread"].terminate()
            update.message.reply_text("Process terminated")
        except KeyError:
            self.logger.warning("Key error")
        except:
            self.logger.error("Something strange in stop")
        
    def text_handler(self, bot, update, user_data):
        try:
            test_function = user_data["testing_f"]
            wait_for = user_data["wait_for"]
            
            if test_function is None:
                raise KeyError("Choose project")
            if wait_for not in user_data["testing_functions"][test_function].args:
                raise KeyError("Choose parameter for change")
            current_value = user_data["testing_functions"][test_function].args[wait_for]
    
            if callable(current_value):
                try:
                    answer = current_value(user_data["testing_functions"][test_function], update.message.text)
                    update.message.reply_text(text=answer)
                    return
                except:
                    raise TypeError("DataTypeError {0}".format(update.message.text))

            elif isinstance(current_value, bool):
                if update.message.text == "False":
                    value = False
                if update.message.text == "True":
                    value = True
            elif isinstance(current_value, float):
                value = float(update.message.text)
            elif isinstance(current_value, int):
                value = int(update.message.text)
            elif isinstance(current_value, str):
                value = update.message.text
            else:
                raise TypeError("DataTypeError {0}".format(update.message.text))

            user_data["testing_functions"][test_function].args[wait_for] = value
            update.message.reply_text(text="New {0} is {1}".format(
                wait_for, user_data["testing_functions"][test_function].args[wait_for]))

        except KeyError:
            update.message.reply_text('Not found')
        except TypeError as t_error:
            update.message.reply_text(t_error)

    def button(self, bot, update, user_data):
        query = update.callback_query
        # Choosing object for tests
        if query.data in self.testing_functions:
            user_data["testing_f"] = query.data
            bot.edit_message_text(text="Set testing function: {0}".format(query.data), 
                chat_id=query.message.chat_id, message_id=query.message.message_id)

        # Choosing parameters
        elif query.data in user_data["testing_functions"][user_data["testing_f"]].args:
            user_data["wait_for"] = query.data
            
            bot.edit_message_text(text="Wait for {0}".format(query.data),
                chat_id=query.message.chat_id, message_id=query.message.message_id)

    @staticmethod
    def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
        if header_buttons:
            menu.insert(0, header_buttons)
        if footer_buttons:
            menu.append(footer_buttons)
        return menu