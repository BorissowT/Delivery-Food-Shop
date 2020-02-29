from flask import Flask
app = Flask(__name__)

from views import *
from admin import *


if __name__ == '__main__':
    app.run()

#####todolist
###autofilling emailspace if logged in
##priceform in account
###registration
###adminaccess
###account buttom
###order fields when userr logged in
###try to split cart route in different functions
###sending email to client
###sending email to cleint from admin
####favico