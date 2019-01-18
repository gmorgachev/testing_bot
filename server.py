import sys
import json

from time import sleep
from lib.testing_bot import TestingBot


with open("./config.json", "r") as f:
    cfg = json.load(f)

bot = TestingBot(cfg)


bot.start_pooling()