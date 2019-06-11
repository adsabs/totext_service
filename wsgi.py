# -*- coding: utf-8 -*-
"""
    wsgi
    ~~~~

    entrypoint wsgi script
"""

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware
from totext import app

if __name__ == "__main__":

    run_simple(
        '0.0.0.0', 4000, app, use_reloader=False, use_debugger=True
    )
