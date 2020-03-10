from flask import Flask
app = Flask(__name__)

from views import *
from admin import *


if __name__ == '__main__':
    app.run()

#####todolist

##priceform in account

###adminaccess
###account buttom

###try to split cart route in different functions
####favico