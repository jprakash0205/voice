# from gevent import monkey; monkey.patch_all()
from base64 import b64decode
import datetime
import json
import os
from urlparse import parse_qsl, urlparse

from flask.ext.bootstrap import Bootstrap

from flask import Flask, Response, abort, request, render_template
from peewee import *
#from playhouse.berkeleydb import BerkeleyDatabase  # Optional.


# 1 pixel GIF, base64-encoded.
BEACON = b64decode('R0lGODlhAQABAIAAANvf7wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==')

# Store the database file in the app directory.
APP_DIR = os.path.dirname(__file__)
DATABASE_NAME = os.path.join(APP_DIR, 'analytics.db')
DOMAIN = 'http://127.0.0.1:5001'  # TODO: change me.

# Simple JavaScript which will be included and executed on the client-side.
JAVASCRIPT = """(function(){
    var d=document,i=new Image,e=encodeURIComponent;
    i.src='%s/a.gif?url='+e(d.location.href)+'&ref='+e(d.referrer)+'&t='+e(d.title)+'&ld='+e(d.location.href);
    })()""".replace('\n', '')

# Flask application settings.
DEBUG = bool(os.environ.get('DEBUG')) or True
SECRET_KEY = 'secret - change me'  # TODO: change me.

app = Flask(__name__)
app.config.from_object(__name__)

database = SqliteDatabase(DATABASE_NAME) # DB Instance

bootstrap = Bootstrap(app) #BootStrap Instance

class JSONField(TextField):
    """Store JSON data in a TextField."""
    def python_value(self, value):
        if value is not None:
            return json.loads(value)

    def db_value(self, value):
        if value is not None:
            return json.dumps(value)

class PageView(Model):
    domain = CharField()
    url = TextField()
    timestamp = DateTimeField(default=datetime.datetime.now, index=True)
    title = TextField(default='')
    ip = CharField(default='')
    referrer = TextField(default='')
    headers = JSONField()
    params = JSONField()

    class Meta:
        database = database

    @classmethod
    def create_from_request(cls):
        parsed = urlparse(request.args['url'])
        params = dict(parse_qsl(parsed.query))
        print(params)

        return PageView.create(
            domain=parsed.netloc,
            url=parsed.path,
            title=request.args.get('t') or '',
            ip=request.headers.get('X-Forwarded-For', request.remote_addr),
            referrer=request.args.get('ref') or '',
            headers=dict(request.headers),
            params=params)

@app.route('/a.gif')
def analyze():
    if not request.args.get('url'):
        abort(404)

    with database.transaction():
        PageView.create_from_request()

    response = Response(app.config['BEACON'], mimetype='image/gif')
    response.headers['Cache-Control'] = 'private, no-cache'
    return response

@app.route('/a.js')
def script():
    return Response(
        app.config['JAVASCRIPT'] % (app.config['DOMAIN']),
        mimetype='text/javascript')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/summary')
def summary():
    tot_cnt = PageView.select().count()
    domain_q = PageView.select(PageView.domain,fn.count(PageView.domain).alias('dms')).group_by(PageView.domain).order_by(fn.count(PageView.domain).desc())
    tpg = PageView.select(PageView.title, fn.Count(PageView.id).alias('tpc')).group_by(PageView.title).order_by(fn.Count(PageView.id).desc()).tuples()
    #domain_cnt = {pv.domain: pv.dms.split(',') for pv in domain_q[:10]}
    #print(domain_cnt)
    return render_template('summary.html',tot_cnt=tot_cnt,domain_q=domain_q,tpg=tpg)

if __name__ == '__main__':
    database.create_tables([PageView], safe=True)
    app.run(port=5001)  # Use Flask's builtin WSGI server.
    # Or for gevent,
    # from gevent.wsgi import WSGIServer
    # WSGIServer(('', 5000), app).serve_forever()
    database.close()