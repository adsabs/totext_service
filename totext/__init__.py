from flask import Flask

app = Flask(__name__)
app.secret_key = 'any random string'
app.config['SECRET_KEY'] = 'you-will-never-guess'

from totext import routes
