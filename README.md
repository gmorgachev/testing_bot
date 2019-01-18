# Testing bot

Telegram bot for run tests on remote computer  
Allow to use phone for creating tasks and checking results

## Install

```bash
git clone https://github.com/gmorgachev/testing_bot.git
pip install python-telegram-bot --upgrade
```

## Configuration

First, you need to set up your TestingBot.
Fill **token** and **chat_id** in *config.json*.

* **token** - token of your bot
* **chat_id** - id of chat with your main telegram account

To execute tests on remote desktop enter the information about remote device in the same file.

## Test Creation

* Implement your test as subclass of **TestingBase** in **candidates.py**

Where,

**params**  - dictionary of test parameters with default value
**args**    - copy of **params** for class instances
**run**     - method which run after start test
**logger**  - need to pass to your **run** method. You will receive logs from this logger

Your can use function as value in **params** to parse complicated params (as pair of *(name, email)* in examples)

## Example

### Sending message for list of people

```python
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
```

### Execution on remote device

To use execution on remote device your must have access to target device via ssh without entering the password (use e.g. *ssh-copy-id*).

```python
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
```

### Running

```bash
python server.py
```