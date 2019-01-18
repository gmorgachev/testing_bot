import logging
import logging.handlers
import json
import os

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
    def send_remote_task(testing, name, token, request_kwargs, chat_id, remote_device):
        cfg = {
            "testing_name": testing.__class__.__name__,
            "name": name,
            "token": token,
            "request_kwargs": request_kwargs,
            "chat_id": chat_id
        }
        with open("./files/remote_cfg", "w") as f:
            json.dump(cfg, f)
        print(testing)
        testing.params_to_dict("./files/remote_params")
        os.system("scp .\\files\\remote_cfg .\\files\\remote_params {0}@{1}:{2}".format(
            remote_device["user"], remote_device["device_name"], remote_device["work_dir"]
        ))
        os.system("ssh {0}@{1} \"{2} {3}\\worker.py {3}\\remote_cfg {3}\\remote_params \" ".format(
            remote_device["user"], remote_device["device_name"], remote_device["interpreter_path"],
            remote_device["work_dir"]))

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


class RemoteWorker(TestingBotRunner):
    @staticmethod
    def remote_run(cfg_file_path, args_file_path):
        with open(cfg_file_path, "r") as f:
            cfg = json.load(f)

        mod = __import__('lib.candidates', fromlist=[cfg["testing_name"]])
        TestingClass = getattr(mod, cfg["testing_name"])
        testing = TestingClass()
        testing.from_dict(args_file_path)
        TestingBotRunner.run(testing, cfg["name"], cfg["token"], cfg["request_kwargs"], cfg["chat_id"])
