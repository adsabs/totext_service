import time
from flask import render_template, session, request, redirect, g, current_app, url_for
from totext.app import app
from totext import api
from totext.forms import ModernForm, PaperForm, ClassicForm
from totext.constants import SERVER_BASE_URL, SORT_OPTIONS
from totext.tools import is_expired


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
        auth = api.bootstrap()
        session['auth'] = { 'access_token': auth['access_token'], 'expire_in': auth['expire_in'] }

@app.route(SERVER_BASE_URL, methods=['GET'])
def index():
    """
    Modern form if no search parameters are sent, otherwise show search results
    """
    form = ModernForm(request.args)
    if len(form.q.data) > 0:
        results = api.search(form.q.data, rows=form.rows.data, start=form.start.data, sort=form.sort.data)
        qtime = "{:.3f}s".format(float(results.get('responseHeader', {}).get('QTime', 0)) / 1000)
        return render_template('search-results.html', base_url=SERVER_BASE_URL, auth=session['auth'], form=form, results=results.get('response'), stats=results.get('stats'), error=results.get('error'), qtime=qtime, sort_options=SORT_OPTIONS)
    return render_template('modern-form.html', base_url=SERVER_BASE_URL, auth=session['auth'], form=form)

@app.route(SERVER_BASE_URL+'classic-form', methods=['GET'])
def classic_form():
    """
    Classic form if no search parameters are sent, otherwise process the parameters
    and redirect to the search results of a built query based on the parameters
    """
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
            query.append("author:({})".format(" OR ".join(["\"{}\"".format(a) for a in authors])))
        elif form.author_logic.data == "AND":
            query.append("author:({})".format(" ".join(["\"{}\"".format(a) for a in authors])))
        else:
            query.append("author:({})".format(" ".join(authors)))
    if form.object_names.data:
        # TODO: form.object_logic.data is not used (not even in BBB)
        objects = form.object_names.data.split()
        results = api.objects_query(objects)
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
    """
    Paper form (left form) if no search parameters are sent, otherwise process the parameters
    and redirect to the search results of a built query based on the parameters
    """
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
    """
    Paper form (right form) if no search parameters are sent, otherwise process the parameters
    and redirect to the search results of a built query based on the parameters
    """
    form = PaperForm()
    if form.bibcodes.data and len(form.bibcodes.data.split()) > 0:
        results = api.store_query(form.bibcodes.data.split()) # Split will get rid of \r\n
        q = "docs({})".format(results['qid'])
        return redirect(url_for('index', q=q))
    return render_template('paper-form.html', base_url=SERVER_BASE_URL, auth=session['auth'], form=form)


@app.route(SERVER_BASE_URL+'abs/<identifier>/abstract', methods=['GET'])
@app.route(SERVER_BASE_URL+'abs/<identifier>', methods=['GET'])
def abs(identifier):
    """
    Show abstrac given an identifier
    """
    results = api.abstract(identifier)
    docs = results.get('response', {}).get('docs', [])
    if len(docs) > 0:
        doc = docs[0]
    else:
        doc= None
        results['error'] = "Record not found."
    return render_template('abstract.html', base_url=SERVER_BASE_URL, auth=session['auth'], doc=doc, error=results.get('error'))

@app.route(SERVER_BASE_URL+'abs/<identifier>/exportcitation', methods=['GET'])
def export(identifier):
    """
    Export bibtex given an identifier
    """
    results = api.abstract(identifier)
    docs = results.get('response', {}).get('docs', [])
    if len(docs) > 0:
        doc = docs[0]
    else:
        doc= None
        results['error'] = "Record not found."
    if 'error' not in results and doc:
        data = api.export_abstract(doc.get('bibcode')).get('export')
    else:
        data = None
    return render_template('abstract-export.html', base_url=SERVER_BASE_URL, auth=session['auth'], data=data, doc=doc, error=results.get('error'))
