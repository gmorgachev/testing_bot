# Testing bot
Program for start long test via telegram


## Install
```bash
pip install python-telegram-bot --upgrade
```

## Usage
Implement your class for test inherited from **TestingBase** in **candidates.py**  
**params** - dictionary of test parameters with default value 
**run** - method which run after start test  
**logger** - need to pass to your method
