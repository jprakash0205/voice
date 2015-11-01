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
DOMAIN = 'http://vocanalytics.cfapps.io/'  # TODO: change me.
#DOMAIN = 'http://vocanalytics.cfapps.io/'  # for CF

# Simple JavaScript which will be included and executed on the client-side.
JAVASCRIPT1 = """(function(){
    var d=document,i=new Image,e=encodeURIComponent,n=navigator,w=window,tt=new Date,tts=tt.getTime();
    var isOpera=!!window.opera||navigator.userAgent.indexOf(" OPR/")>=0,isFirefox="undefined"!=typeof InstallTrigger,isSafari=Object.prototype.toString.call(window.HTMLElement).indexOf("Constructor")>0,isChrome=!!window.chrome&&!isOpera,isIE=!!document.documentMode,b="";b=isIE?"IE":isChrome?"Chrome":isFirefox?"Firefox":isOpera?"Opera":isSafari?"Safari":"";
    i.src='%s/b.gif?url='+e(d.location.href)+'&ref='+e(d.referrer)+'&t='+e(d.title)+'&ck='+e(d.cookie)+'&lm='+e(d.lastModified)+'&an='+e(b)+'&ld='+e(tts);
    })()""".replace('\n', '')

JAVASCRIPT = """window.onload=function(){var e=document,n=new Image,o=encodeURIComponent,t=(navigator,window),r=!!window.opera||navigator.userAgent.indexOf(" OPR/")>=0,i="undefined"!=typeof InstallTrigger,a=Object.prototype.toString.call(window.HTMLElement).indexOf("Constructor")>0,d=!!window.chrome&&!r,c=!!document.documentMode,f="";f=c?"IE":d?"Chrome":i?"Firefox":r?"Opera":a?"Safari":"";
var m=(t.performance.timing.domContentLoadedEventEnd-t.performance.timing.navigationStart)/1e3;
var OSName="Unknown OS";-1!=navigator.appVersion.indexOf("Win")&&(OSName="Windows"),-1!=navigator.appVersion.indexOf("Mac")&&(OSName="MacOS"),-1!=navigator.appVersion.indexOf("X11")&&(OSName="UNIX"),-1!=navigator.appVersion.indexOf("Linux")&&(OSName="Linux");
n.src="%s/a.gif?url="+o(e.location.href)+"&ref="+o(e.referrer)+"&t="+o(e.title)+"&ck="+o(e.cookie)+"&lm="+o(e.lastModified)+"&an="+o(f)+"&ld="+o(m)+"&regt="+o(OSName)};
""".replace('\n', '')

# Flask application settings.
DEBUG = bool(os.environ.get('DEBUG')) or True
SECRET_KEY = 'secret - change me'  # TODO: change me.
PORT = 5010

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
    cookies = TextField(default='')
    docmodified = TextField(default='')
    bappname = TextField(default='')
    loadtime = TextField(default='')
    timespent = TextField(default='')
    regtry = TextField(default='')
    headers = JSONField()
    params = JSONField()

    class Meta:
        database = database

    @classmethod
    def create_from_request(cls):
        parsed = urlparse(request.args['url'])
        params = dict(parse_qsl(parsed.query))

        return PageView.create(
            domain=parsed.netloc,
            url=parsed.path,
            title=request.args.get('t') or '',
            ip=request.headers.get('X-Forwarded-For', request.remote_addr),
            referrer=request.args.get('ref') or '',
            cookies = request.args.get('ck') or '',
            docmodified = request.args.get('lm') or '',
            bappname = request.args.get('an') or '',
            loadtime = request.args.get('ld') or '',
            timespent = request.args.get('ts') or '',
            regtry = request.args.get('regt') or '',
            headers=dict(request.headers),
            params=params)

    @classmethod
    def update_from_request(cls):
        parsed = urlparse(request.args['url'])
        params = dict(parse_qsl(parsed.query))
        rid = PageView.select(PageView.id).order_by(PageView.id.desc()).get()

        return PageView.update(
            domain=parsed.netloc,
            url=parsed.path,
            title=request.args.get('t') or '',
            ip=request.headers.get('X-Forwarded-For', request.remote_addr),
            referrer=request.args.get('ref') or '',
            cookies = request.args.get('ck'),
            docmodified = request.args.get('lm'),
            bappname = request.args.get('an'),
            loadtime = request.args.get('ld'),
            timespent = request.args.get('ts'),
            regtry = request.args.get('regt'),
            headers=dict(request.headers),
            params=params).where(
            PageView.id==rid
            )    


@app.route('/a.gif')
def analyze():
    if not request.args.get('url'):
        abort(404)

    with database.transaction():
        PageView.create_from_request()

    response = Response(app.config['BEACON'], mimetype='image/gif')
    response.headers['Cache-Control'] = 'private, no-cache'
    return response

@app.route('/b.gif')
def analyze_b():
    if not request.args.get('url'):
        abort(404)

    with database.transaction():
        PageView.update_from_request()

    response = Response(app.config['BEACON'], mimetype='image/gif')
    response.headers['Cache-Control'] = 'private, no-cache'
    return response

@app.route('/a.js')
def script():
    return Response(
        app.config['JAVASCRIPT'] % (app.config['DOMAIN']),
        mimetype='text/javascript')

@app.route('/b.js')
def script1():
    return Response(
        app.config['JAVASCRIPT1'] % (app.config['DOMAIN']),
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
    domain_q = PageView.select(PageView.domain,fn.count(PageView.domain).alias('dms')).where(PageView.domain != '').group_by(PageView.domain).order_by(fn.count(PageView.domain).desc())
    tpg = PageView.select(PageView.title, fn.Count(PageView.id).alias('tpc')).group_by(PageView.title).order_by(fn.Count(PageView.id).desc()).tuples()
    tpg_m = PageView.select(PageView.title,PageView.docmodified, fn.Count(PageView.id).alias('tpc')).group_by(PageView.title,PageView.docmodified).order_by(fn.Count(PageView.id).desc()).tuples()
    appname = PageView.select(PageView.bappname, fn.Count(PageView.id).alias('appcnt')).group_by(PageView.bappname).order_by(fn.Count(PageView.id).desc()).tuples()
    tref = PageView.select(PageView.referrer, fn.Count(PageView.id).alias('refcnt')).group_by(PageView.referrer).order_by(fn.Count(PageView.id).desc()).tuples()
    tip = PageView.select(PageView.ip, fn.Count(PageView.id).alias('ipcnt')).where(PageView.ip != '').group_by(PageView.ip).order_by(fn.Count(PageView.id).desc()).tuples()
    uqip = PageView.select(PageView.ip).group_by(PageView.ip).count()
    hour = fn.date_part('hour', PageView.timestamp)
    id_count = fn.Count(PageView.id)
    mthr = PageView.select(hour.alias('hour'), id_count.alias('hcnt')).group_by(hour).order_by(hour.asc()).dicts()
    bname = PageView.select(PageView.bappname.alias('brow'), fn.Count(PageView.id).alias('browcnt')).group_by(PageView.bappname).order_by(fn.Count(PageView.id).desc()).dicts()
    day = fn.date_part('day', PageView.timestamp)
    dmthr = PageView.select(day.alias('day'), id_count.alias('dycnt')).group_by(day).order_by(day.asc()).dicts()
    tot_dm = PageView.select(PageView.domain,fn.count(PageView.domain)).where(PageView.domain != '').group_by(PageView.domain).count()
    pgtk = PageView.select(PageView.title,fn.count(PageView.title)).where(PageView.title != '').group_by(PageView.domain).count()
    return render_template('summary.html',tot_cnt=tot_cnt,domain_q=domain_q,tpg=tpg,tpg_m=tpg_m,appname=appname,tref=tref,tip=tip,uqip=uqip,mthr=mthr,bname=bname,dmthr=dmthr,tot_dm=tot_dm,pgtk=pgtk)

@app.route('/vocnews')
def vocnews():
    pl = PageView.select(PageView.title,fn.Min(PageView.loadtime).alias('mload')).where((PageView.loadtime != '') & (PageView.domain == 'vocnews.cfapps.io')).group_by(PageView.title).order_by(fn.Min(PageView.loadtime).asc()).dicts()
    tpg = PageView.select(PageView.title, fn.Count(PageView.id).alias('tpc')).where((PageView.title != '') & (PageView.domain == 'vocnews.cfapps.io')).group_by(PageView.title).order_by(fn.Count(PageView.id).desc()).tuples()
    tpg_m = PageView.select(PageView.title,fn.Max(PageView.docmodified)).where((PageView.title != '') & (PageView.domain == 'vocnews.cfapps.io')).group_by(PageView.title).order_by(fn.Count(PageView.id).desc()).tuples()
    appname = PageView.select(PageView.bappname, fn.Count(PageView.id).alias('appcnt')).where((PageView.bappname != '') & (PageView.domain == 'vocnews.cfapps.io')).group_by(PageView.bappname).order_by(fn.Count(PageView.id).desc()).tuples()
    tref = PageView.select(PageView.referrer, fn.Count(PageView.id).alias('refcnt')).where((PageView.referrer != '') & (PageView.domain == 'vocnews.cfapps.io')).group_by(PageView.referrer).order_by(fn.Count(PageView.id).desc()).tuples()
    tip = PageView.select(PageView.ip, fn.Count(PageView.id).alias('ipcnt')).where((PageView.ip != '') & (PageView.domain == 'vocnews.cfapps.io')).group_by(PageView.ip).order_by(fn.Count(PageView.id).desc()).tuples()
    hour = fn.date_part('hour', PageView.timestamp)
    id_count = fn.Count(PageView.id)
    mthr = PageView.select(hour.alias('hour'), id_count.alias('hcnt')).where(PageView.domain == 'vocnews.cfapps.io').group_by(hour).order_by(hour.asc()).dicts()
    bname = PageView.select(PageView.bappname.alias('brow'), fn.Count(PageView.id).alias('browcnt')).where((PageView.bappname != '') & (PageView.domain == 'vocnews.cfapps.io')).group_by(PageView.bappname).order_by(fn.Count(PageView.id).desc()).dicts()
    day = fn.date_part('day', PageView.timestamp)
    dmthr = PageView.select(day.alias('day'), id_count.alias('dycnt')).where(PageView.domain == 'vocnews.cfapps.io').group_by(day).order_by(day.asc()).dicts()
    tos = PageView.select(PageView.regtry.alias('osname'),fn.Count(PageView.id).alias('oscnt')).where((PageView.regtry != '') & (PageView.domain == 'vocnews.cfapps.io')).group_by(PageView.regtry).order_by(fn.Count(PageView.id).desc()).dicts()
    hd = PageView.select(PageView.headers,fn.Count(PageView.id).alias('uacnt')).where((PageView.headers != '') & (PageView.domain == 'vocnews.cfapps.io')).group_by(PageView.headers).order_by(fn.Count(PageView.id).desc()).tuples()
    return render_template('report.html',rpt='VOC News',pl=pl,tpg=tpg,tpg_m=tpg_m,appname=appname,tref=tref,tip=tip,mthr=mthr,bname=bname,dmthr=dmthr,tos=tos,hd=hd)

@app.route('/vocinfo')
def vocinfo():
    pl = PageView.select(PageView.title,fn.Min(PageView.loadtime).alias('mload')).where((PageView.loadtime != '') & (PageView.domain == 'vocinfo.cfapps.io')).group_by(PageView.title).order_by(fn.Min(PageView.loadtime).asc()).dicts()
    tpg = PageView.select(PageView.title, fn.Count(PageView.id).alias('tpc')).where((PageView.title != '') & (PageView.domain == 'vocinfo.cfapps.io')).group_by(PageView.title).order_by(fn.Count(PageView.id).desc()).tuples()
    tpg_m = PageView.select(PageView.title,fn.Max(PageView.docmodified)).where((PageView.title != '') & (PageView.domain == 'vocinfo.cfapps.io')).group_by(PageView.title).order_by(fn.Count(PageView.id).desc()).tuples()
    appname = PageView.select(PageView.bappname, fn.Count(PageView.id).alias('appcnt')).where((PageView.bappname != '') & (PageView.domain == 'vocinfo.cfapps.io')).group_by(PageView.bappname).order_by(fn.Count(PageView.id).desc()).tuples()
    tref = PageView.select(PageView.referrer, fn.Count(PageView.id).alias('refcnt')).where((PageView.referrer != '') & (PageView.domain == 'vocinfo.cfapps.io')).group_by(PageView.referrer).order_by(fn.Count(PageView.id).desc()).tuples()
    tip = PageView.select(PageView.ip, fn.Count(PageView.id).alias('ipcnt')).where((PageView.ip != '') & (PageView.domain == 'vocinfo.cfapps.io')).group_by(PageView.ip).order_by(fn.Count(PageView.id).desc()).tuples()
    hour = fn.date_part('hour', PageView.timestamp)
    id_count = fn.Count(PageView.id)
    mthr = PageView.select(hour.alias('hour'), id_count.alias('hcnt')).where(PageView.domain == 'vocinfo.cfapps.io').group_by(hour).order_by(hour.asc()).dicts()
    bname = PageView.select(PageView.bappname.alias('brow'), fn.Count(PageView.id).alias('browcnt')).where((PageView.bappname != '') & (PageView.domain == 'vocinfo.cfapps.io')).group_by(PageView.bappname).order_by(fn.Count(PageView.id).desc()).dicts()
    day = fn.date_part('day', PageView.timestamp)
    dmthr = PageView.select(day.alias('day'), id_count.alias('dycnt')).where(PageView.domain == 'vocinfo.cfapps.io').group_by(day).order_by(day.asc()).dicts()
    tos = PageView.select(PageView.regtry.alias('osname'),fn.Count(PageView.id).alias('oscnt')).where((PageView.regtry != '') & (PageView.domain == 'vocinfo.cfapps.io')).group_by(PageView.regtry).order_by(fn.Count(PageView.id).desc()).dicts()
    hd = PageView.select(PageView.headers,fn.Count(PageView.id).alias('uacnt')).where((PageView.headers != '') & (PageView.domain == 'vocinfo.cfapps.io')).group_by(PageView.headers).order_by(fn.Count(PageView.id).desc()).tuples()
    return render_template('report.html',rpt='VOC Info',pl=pl,tpg=tpg,tpg_m=tpg_m,appname=appname,tref=tref,tip=tip,mthr=mthr,bname=bname,dmthr=dmthr,tos=tos,hd=hd)

if __name__ == '__main__':
    database.create_tables([PageView], safe=True)
    app.run(host='0.0.0.0',port=5002)  # Use Flask's builtin WSGI server.
    database.close()
