import os
from flask import Flask

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'any random string')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'you-will-never-guess')

from totext import routes
