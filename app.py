from flask import Flask
app = Flask(__name__)

from views import *
from admin import *


if __name__ == '__main__':
    app.run()

