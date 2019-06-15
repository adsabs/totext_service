from flask import render_template, session, request, redirect, g, current_app, url_for
from totext import app
from totext.forms import ModernForm, PaperForm, ClassicForm
from datetime import datetime
import urllib
import time
import os

PRODUCTION_URL = "https://prod.adsabs.harvard.edu/"
DEVELOPMENT_URL = "https://dev.adsabs.harvard.edu/"
ADS_URL = DEVELOPMENT_URL
API_URL = ADS_URL+"v1/"
SERVER_BASE_URL = os.environ.get('SERVER_BASE_URL', "/")
BOOTSTRAP_SERVICE = os.environ.get('BOOTSTRAP_SERVICE', API_URL+"accounts/bootstrap")
SEARCH_SERVICE = os.environ.get('SEARCH_SERVICE', API_URL+"search/query")
EXPORT_SERVICE = os.environ.get('EXPORT_SERVICE', API_URL+"export/bibtex")
VAULT_SERVICE = os.environ.get('VAULT_SERVICE', API_URL+"vault/query")
OBJECTS_SERVICE = os.environ.get('OBJECTS_SERVICE', API_URL+"objects/query")
ESOURCE_SERVICE = os.environ.get('ESOURCE_SERVICE', API_URL+"resolver/{}/esource")
API_TIMEOUT = 30
SORT_OPTIONS = [
    { 'id': 'author_count', 'text': 'Authors', 'description': 'sort by number of authors' },
    { 'id': 'bibcode', 'text': 'Bibcode', 'description': 'sort by bibcode' },
    { 'id': 'citation_count', 'text': 'Citations', 'description': 'sort by number of citations' },
    { 'id': 'citation_count_norm', 'text': 'Norm. Citations', 'description': 'sort by number of normalized citations' },
    { 'id': 'classic_factor', 'text': 'Classic Factor', 'description': 'sort using classical score' },
    { 'id': 'first_author', 'text': 'First Author', 'description': 'sort by first author' },
    { 'id': 'date', 'text': 'Date', 'description': 'sort by publication date' },
    { 'id': 'entry_date', 'text': 'Entry Date', 'description': 'sort by date work entered the database' },
    { 'id': 'read_count', 'text': 'Reads', 'description': 'sort by number of reads' },
    { 'id': 'score', 'text': 'Score', 'description': 'sort by the relative score' }
]

def is_expired(auth):
    expire_in = datetime.strptime(auth['expire_in'], "%Y-%m-%dT%H:%M:%S.%f")
    delta = expire_in - datetime.now()
    return delta.total_seconds() < 0

@app.before_request
def before_request():
    """
    Store API anonymous cookie in session or if it exists, check if it has expired
    """
    g.request_start_time = time.time()
    g.request_time = lambda: "{:.3f}s".format((time.time() - g.request_start_time))
    if 'cookies' not in session:
        session['cookies'] = {}
    if 'auth' not in session or is_expired(session['auth']):
        # Example of session['auth'] content:
        #   {'username': 'anonymous@ads', 'scopes': ['execute-query', 'store-query'],
        #   'client_id': 'DpRqNMLSv9Rqjycpz1XTzLH8ZZunQ4KY5ynagmEg', 'access_token': '7vIASALjYla1ddaFD6A258bH1KfyPiKQ7l5RBSi2',
        #   'client_name': 'BB client', 'token_type': 'Bearer', 'ratelimit': 1.0, 'anonymous': True,
        #   'client_secret': '2yvOxfgZtBaiNzAGt2YYYhMKyhTxIFxS62rFtcxNdjEDqWu0w33vQhp41RaQ',
        #   'expire_in': '2019-06-12T14:15:17.823482', 'refresh_token': 'itRUeo3vshekgyMYNMDxoGb84C6NTYoqjQ156xO9'}
        r = current_app.client.get(BOOTSTRAP_SERVICE, cookies=session['cookies'], timeout=API_TIMEOUT, verify=False)
        r.raise_for_status()
        r.cookies.clear_expired_cookies()
        session['cookies'].update(r.cookies.get_dict())
        auth = r.json()
        session['auth'] = { 'access_token': auth['access_token'], 'expire_in': auth['expire_in'] }

def abstract(bibcode):
    """
    Retrieve abstract
    """
    headers = { "Authorization": "Bearer:{}".format(session['auth']['access_token']), }
    params = urllib.urlencode({
            'fl': 'title,bibcode,author,pub,pubdate,abstract,citation_count,[citations],read_count,esources,property',
            'q': 'bibcode:{0}'.format(bibcode),
            'rows': '25',
            'sort': 'date desc, bibcode desc',
            'start': '0'
            })
    r = current_app.client.get(SEARCH_SERVICE + "?" + params, headers=headers, cookies=session['cookies'], timeout=API_TIMEOUT, verify=False)
    r.raise_for_status()
    r.cookies.clear_expired_cookies()
    session['cookies'].update(r.cookies.get_dict())
    return r.json()

def export_abstract(bibcode):
    """
    Export bibtex
    """
    headers = { "Authorization": "Bearer:{}".format(session['auth']['access_token']), }
    data = {
            'bibcode': ['{0}'.format(bibcode)],
            'sort': 'date desc, bibcode desc',
            }
    r = current_app.client.post(EXPORT_SERVICE, json=data, headers=headers, cookies=session['cookies'], timeout=API_TIMEOUT, verify=False)
    r.raise_for_status()
    r.cookies.clear_expired_cookies()
    session['cookies'].update(r.cookies.get_dict())
    return r.json()

def store_query(bibcodes, sort="date desc, bibcode desc"):
    """
    Store query in vault
    """
    headers = { "Authorization": "Bearer:{}".format(session['auth']['access_token']), }
    data = {
                'bigquery': ["bibcode\n"+"\n".join(bibcodes)],
                'fq': ["{!bitset}"],
                'q': ["*:*"],
                'sort': [sort]
            }
    r = current_app.client.post(VAULT_SERVICE, json=data, headers=headers, cookies=session['cookies'], timeout=API_TIMEOUT, verify=False)
    r.raise_for_status()
    r.cookies.clear_expired_cookies()
    session['cookies'].update(r.cookies.get_dict())
    return r.json()

def objects_query(object_names):
    """
    Transform object into ID
    """
    headers = { "Authorization": "Bearer:{}".format(session['auth']['access_token']) }
    data = {
                'query': ["object:({})".format(",".join(object_names))],
            }
    r = current_app.client.post(OBJECTS_SERVICE, json=data, headers=headers, cookies=session['cookies'], timeout=API_TIMEOUT, verify=False)
    r.raise_for_status()
    r.cookies.clear_expired_cookies()
    session['cookies'].update(r.cookies.get_dict())
    return r.json()

def search(q, rows=25, start=0, sort="date desc"):
    """
    Execute query
    """
    headers = { "Authorization": "Bearer:{}".format(session['auth']['access_token']), }
    if "bibcode desc" not in sort:
        # Add secondary sort criteria
        sort += ", bibcode desc"
    if "citation_count_norm" in sort:
        stats = 'true'
        stats_field = 'citation_count_norm'
    elif "citation_count" in sort:
        stats = 'true'
        stats_field = 'citation_count'
    else:
        stats = 'false'
        stats_field = ''
    params = urllib.urlencode({
                    'fl': 'title,bibcode,author,citation_count,pubdate,[citations]',
                    'q': '{0}'.format(q.encode("utf-8")),
                    'rows': '{0}'.format(rows),
                    'sort': '{0}'.format(sort),
                    'start': '{0}'.format(start),
                    'stats': stats,
                    'stats.field': stats_field
                })
    r = current_app.client.get(SEARCH_SERVICE + "?" + params, headers=headers, cookies=session['cookies'], timeout=API_TIMEOUT, verify=False)
    r.raise_for_status()
    r.cookies.clear_expired_cookies()
    session['cookies'].update(r.cookies.get_dict())
    return r.json()

@app.route(SERVER_BASE_URL, methods=['GET'])
def index():
    form = ModernForm(request.args)
    if len(form.q.data) > 0:
        results = search(form.q.data, rows=form.rows.data, start=form.start.data, sort=form.sort.data)
        for i in xrange(len(results['response']['docs'])):
            results['response']['docs'][i]['reference_count'] = results['response']['docs'][i]['[citations]']['num_references']
        qtime = "{:.3f}s".format(float(results['responseHeader']['QTime']) / 1000)
        return render_template('search.html', base_url=SERVER_BASE_URL, auth=session['auth'], form=form, results=results['response'], stats=results.get('stats'), qtime=qtime, sort_options=SORT_OPTIONS)
    return render_template('modern-form.html', base_url=SERVER_BASE_URL, auth=session['auth'], form=form)

@app.route(SERVER_BASE_URL+'classic-form', methods=['GET'])
def classic_form():
    form = ClassicForm(request.args)
    query = []
    if form.astronomy.data:
        query.append("database:astronomy")
    if form.physics.data:
        query.append("database:physics")
    if query:
        query = [" OR ".join(query)]
    if form.refereed.data:
        query.append("property:refereed")
    if form.article.data:
        query.append("property:article")
    if form.author_names.data:
        authors = form.author_names.data.split()
        if form.author_logic.data == "OR":
            query.append(" OR ".join(["author:({})".format(a) for a in authors]))
        elif form.author_logic.data == "AND":
            query.append(" ".join(["author:({})".format(a) for a in authors]))
        else:
            query.append("author:({})".format(" ".join(authors)))
    if form.object_names.data:
        # TODO: form.object_logic.data is not used (not even in BBB)
        objects = form.object_names.data.split()
        results = objects_query(objects)
        transformed_objects_query = results.get('query')
        if transformed_objects_query:
            query.append(transformed_objects_query)
    year_from = min(max(form.year_from.data, 0), 9999) if form.year_from.data else 0
    year_to = min(max(form.year_to.data, 0), 9999) if form.year_to.data else 9999
    month_from = min(max(form.month_from.data, 1), 12) if form.month_from.data else 1
    month_to = min(max(form.month_to.data, 1), 12) if form.month_to.data else 12
    pubdate = "pubdate:[{:04}-{:02} TO {:04}-{:02}]".format(year_from, month_from, year_to, month_to)
    if pubdate != "pubdate:[0000-01 TO 9999-12]":
        query.append(pubdate)
    if form.title.data:
        titles = form.title.data.split()
        if form.title_logic.data == "OR":
            query.append(" OR ".join(["title:({})".format(a) for a in titles]))
        elif form.title_logic.data == "AND":
            query.append(" ".join(["title:({})".format(a) for a in titles]))
        else:
            query.append("title:({})".format(" ".join(titles)))
    if form.abstract.data:
        abstracts = form.abstract.data.split()
        if form.abstract_logic.data == "OR":
            query.append(" OR ".join(["abstract:({})".format(a) for a in abstracts]))
        elif form.abstract_logic.data == "AND":
            query.append(" ".join(["abstract:({})".format(a) for a in abstracts]))
        else:
            query.append("abs:({})".format(" ".join(abstracts)))

    if form.bibstem.data:
        bibstems = form.bibstem.data.split(",")
        query.append(" OR ".join(["bibstem:({})".format(b) for b in bibstems]))

    if query:
        return redirect(url_for('index', q=" ".join(query)))
    else:
        return render_template('classic-form.html', base_url=SERVER_BASE_URL, auth=session['auth'], form=form)

@app.route(SERVER_BASE_URL+'paper-form', methods=['GET'])
def paper_form():
    form = PaperForm(request.args)
    query = []
    if form.bibstem.data:
        query.append("bibstem:({})".format(form.bibstem.data))
    if form.year.data:
        query.append("year:{}".format(form.year.data))
    if form.volume.data:
        query.append("volume:{}".format(form.volume.data))
    if form.page.data:
        query.append("page:{}".format(form.page.data))
    if query:
        return redirect(url_for('index', q=" ".join(query)))
    else:
        return render_template('paper-form.html', base_url=SERVER_BASE_URL, auth=session['auth'], form=form)

@app.route(SERVER_BASE_URL+'paper-form', methods=['POST'])
def paper_form_bibcodes():
    form = PaperForm()
    if form.bibcodes.data and len(form.bibcodes.data.split()) > 0:
        results = store_query(form.bibcodes.data.split()) # Split will get rid of \r\n
        q = "docs({})".format(results['qid'])
        return redirect(url_for('index', q=q))
    return render_template('paper-form.html', base_url=SERVER_BASE_URL, auth=session['auth'], form=form)


@app.route(SERVER_BASE_URL+'abs/<bibcode>/abstract', methods=['GET'])
@app.route(SERVER_BASE_URL+'abs/<bibcode>', methods=['GET'])
def abs(bibcode):
    if len(bibcode) == 19:
        results = abstract(bibcode)
        results['response']['docs'][0]['reference_count'] = results['response']['docs'][0]['[citations]']['num_references']
        return render_template('abstract.html', base_url=SERVER_BASE_URL, auth=session['auth'], doc=results['response']['docs'][0])
    return redirect(url_for('index'))

@app.route(SERVER_BASE_URL+'abs/<bibcode>/export', methods=['GET'])
def export(bibcode):
    if len(bibcode) == 19:
        results = abstract(bibcode)
        results['response']['docs'][0]['reference_count'] = results['response']['docs'][0]['[citations]']['num_references']
        data = export_abstract(bibcode)
        return render_template('export.html', base_url=SERVER_BASE_URL, auth=session['auth'], data=data['export'], doc=results['response']['docs'][0])
    return redirect(url_for('index'))
