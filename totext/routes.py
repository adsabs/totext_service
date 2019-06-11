from flask import render_template, session
from totext import app
from datetime import datetime
import requests

PRODUCTION_URL = "https://prod.adsabs.harvard.edu/"
DEVELOPMENT_URL = "https://dev.adsabs.harvard.edu/"
ADS_URL = DEVELOPMENT_URL
API_URL = ADS_URL+"v1/"
BOOTSTRAP_SERVICE = API_URL+"accounts/bootstrap"
API_TIMEOUT = 30

def is_expired(auth):
    expire_in = datetime.strptime(auth['expire_in'], "%Y-%m-%dT%H:%M:%S.%f")
    delta = expire_in - datetime.now()
    return delta.seconds < 0

@app.before_request
def before_request():
    """
    Store API anonymous cookie in session or if it exists, check if it has expired
    """
    if 'cookies' not in session:
        session['cookies'] = {}
    if 'auth' not in session or is_expired(session['auth']):
        # Example of session['auth'] content:
        #   {'username': 'anonymous@ads', 'scopes': ['execute-query', 'store-query'],
        #   'client_id': 'DpRqNMLSv9Rqjycpz1XTzLH8ZZunQ4KY5ynagmEg', 'access_token': '7vIASALjYla1ddaFD6A258bH1KfyPiKQ7l5RBSi2',
        #   'client_name': 'BB client', 'token_type': 'Bearer', 'ratelimit': 1.0, 'anonymous': True,
        #   'client_secret': '2yvOxfgZtBaiNzAGt2YYYhMKyhTxIFxS62rFtcxNdjEDqWu0w33vQhp41RaQ',
        #   'expire_in': '2019-06-12T14:15:17.823482', 'refresh_token': 'itRUeo3vshekgyMYNMDxoGb84C6NTYoqjQ156xO9'}
        r = requests.get(BOOTSTRAP_SERVICE, cookies=session['cookies'], timeout=API_TIMEOUT)
        r.raise_for_status()
        if r.ok:
            r.cookies.clear_expired_cookies()
            session['cookies'].update(r.cookies.get_dict())
            session['auth'] = r.json()

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Totext home', auth=session['auth'])
    #return "Hello, World!"
