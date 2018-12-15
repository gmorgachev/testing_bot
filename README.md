# Testing bot
Telegram bot for run tests on remote PC  


## Install
```bash
git clone https://github.com/gmorgachev/testing_bot.git
pip install python-telegram-bot --upgrade
```

## Server workflow
- Implement your test as class inherited from **TestingBase** in **candidates.py**
- Run **main.py**

**params**  - dictionary of test parameters with default value 
**run**     - method which run after start test  
**logger**  - need to pass to your method


