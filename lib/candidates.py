import sys
import re
import json

from time import sleep

class TestingBase:
    params = {}

    def __init__(self):
        return

    def run(self, logger):
        raise NotImplementedError()

class RemoteTestingBase(TestingBase):
    params = {}

    def __init__(self):
        return

    def params_to_dict(self):
        raise NotImplementedError()

    @staticmethod
    def from_dict(path_to_file):
        raise NotImplementedError()


class TestingExample(TestingBase):
    params = {
        "n": 3
    }

    def __init__(self):
        self.args = MessageToUsers.params
        return

    def run(self, logger):
        for i in range(self.params["n"]):
            sleep(4)
            logger.warning(i)


class MessageToUsers(TestingBase):
    @staticmethod
    def send_email(name, email, text):
        sleep(0.1)
        return

    def add_recipient(self, input):
        name, email = re.split(pattern=", ", string=input)
        self.recipient[name] = email
        return "Added {0} {1} ".format(name, email)

    params = {
        "n": 3,
        "text": "Hello",
        "add_recipient": add_recipient
    }

    def __init__(self):
        self.args = MessageToUsers.params
        self.recipient = {}
        return

    def run(self, logger):
        for name in self.recipient:
            MessageToUsers.send_email(name, self.recipient[name], self.args["text"])
            logger.warning("Send {0} to {1} ({2})".format(self.params["text"], self.recipient[name], name))

class MessageToUsersRemote(RemoteTestingBase):
    @staticmethod
    def send_email(name, email, text):
        sleep(0.1)
        return

    def add_recipient(self, input):
        name, email = re.split(pattern=", ", string=input)
        self.recipient[name] = email
        return "Added {0} {1} ".format(name, email)

    params = {
        "n": 3,
        "text": "Hello",
        "add_recipient": add_recipient
    }

    def __init__(self):
        self.args = MessageToUsers.params
        self.recipient = {}
        return

    def run(self, logger):
        for name in self.recipient:
            MessageToUsers.send_email(name, self.recipient[name], self.args["text"])
            logger.warning("Send {0} to {1} ({2})".format(self.params["text"], self.recipient[name], name))

    def params_to_dict(self, path):
        print(self.recipient)
        saved_dict = {"args": self.args, "recipient": self.recipient}
        del saved_dict["args"]["add_recipient"]
        with open(path, 'w') as f:
            json.dump(saved_dict, f)
        
        self.args["add_recipient"] = MessageToUsersRemote.add_recipient

    def from_dict(self, path):
        with open(path, 'r') as f:
            saved_dict = json.load(f)
        self.args = saved_dict["args"]
        self.recipient = saved_dict["recipient"]
        self.args["add_recipient"] = MessageToUsersRemote.add_recipient