from flask import Flask

app = Flask(__name__)
app.secret_key = 'any random string'

from totext import routes
