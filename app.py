import os
import json
import datetime

from flask import Flask, url_for, redirect, \
    render_template, session, request, Response, \
    flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from models import Burndown, get_all
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError
from oauth2client.client import verify_id_token
from oauth2client.crypt import AppIdentityError


import ssl
from urllib import urlopen

basedir = os.path.abspath(os.path.dirname(__file__))


"""App Configuration"""


class Auth:
    """Google Project Credentials"""
    CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
    CLIENT_SECRET = os.environ['GOOGLE_CLIENT_SECRET']
    DCC_DASHBOARD_HOST = 'localhost'
    DCC_DASHBOARD_PORT = '5000'
    DCC_DASHBOARD_PROTOCOL = 'https'
    if 'DCC_DASHBOARD_HOST' in os.environ.keys():
        DCC_DASHBOARD_HOST = os.environ['DCC_DASHBOARD_HOST']
    if 'DCC_DASHBOARD_PORT' in os.environ.keys():
        DCC_DASHBOARD_PORT = os.environ['DCC_DASHBOARD_PORT']
    if 'DCC_DASHBOARD_PROTOCOL' in os.environ.keys():
        DCC_DASHBOARD_PROTOCOL = os.environ['DCC_DASHBOARD_PROTOCOL']
    REDIRECT_URI = DCC_DASHBOARD_PROTOCOL+'://'+DCC_DASHBOARD_HOST+'/gCallback'
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
    SCOPE = ['profile', 'email']


class Config:
    """Base config"""
    APP_NAME = "Test Google Login"
    SECRET_KEY = os.environ.get("SECRET_KEY") or "somethingsecret"


class DevConfig(Config):
    """Dev config"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, "test.db")


class ProdConfig(Config):
    """Production config"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@login-db/{}'.format(
                               os.getenv("L_POSTGRES_USER"),
                               os.getenv("L_POSTGRES_PASSWORD"),
                               os.getenv("L_POSTGRES_DB"))


config = {
    "dev": DevConfig,
    "prod": ProdConfig,
    "default": DevConfig
}


"""APP creation and configuration"""
app = Flask(__name__)
app.config.from_object(config['prod'])
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"
es_service = os.environ.get("ES_SERVICE", "localhost")
es = Elasticsearch(['http://'+es_service+':9200/'])


""" DB Models """


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(200))
    access_token = db.Column(db.String(5000))
    redwood_token = db.Column(db.String(5000))
    tokens = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


""" OAuth Session creation """


def get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(Auth.CLIENT_ID, token=token)
    if state:
        return OAuth2Session(
            Auth.CLIENT_ID,
            state=state,
            redirect_uri=Auth.REDIRECT_URI)
    oauth = OAuth2Session(
        Auth.CLIENT_ID,
        redirect_uri=Auth.REDIRECT_URI,
        scope=Auth.SCOPE)
    return oauth


def query_es_rna_seq(es_object, index, query_params, cardinality):
    """
GET burn_idx/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "regexp": {
            "experimentalStrategy": "[rR][nN][aA][-][Ss][Ee][Qq]"
          }
        },{
          "regexp":{
            "software": "[Ss]pinnaker"
          }
        }
      ]
    }
  },
  "aggs": {
    "filtered_jobs":{
      "cardinality": {
        "field": "repoDataBundleId"
      }
    }
  }
}
    Pass a list of tuples?
    [('regexp', 'experimentalStrategy', '[my][pattern]'), (...)...]
    reduce('function', 'iterate', 'initializer')
    """
    # Create search obejct
    s = Search(using=es_object, index=index)
    # Add the queries
    s = reduce(lambda s, x: s.query(x[0], **{x[1]: x[2]}), query_params, s)
    # Add the aggregates
    s.aggs.metric("filtered_jobs", 'cardinality', field=cardinality,
                  precision_threshold="40000")
    # Execute the query
    response = s.execute()
    return response.aggregations.filtered_jobs.value


def burndown():
    """
    Method for parsing the plot points and
    returning them as appropriate.
    """
    total_jobs = [int(x.total_jobs) for x in get_all()]
    finished_jobs = [int(x.finished_jobs) for x in get_all()]
    captured_dates = [x.captured_date for x in get_all()]
    return (total_jobs, finished_jobs, captured_dates)


@app.route('/')
def index():
    """
    Render the main page.
    """
    return render_template('index.html')


@app.route('/<name>.html')
def html_rend(name):
    """
    Render templates based on their name.
    Handle the templates differently depending
    on its name.
    """
    data = os.environ['DCC_DASHBOARD_SERVICE']
    coreClientVersion = os.getenv('DCC_CORE_CLIENT_VERSION', '1.1.0')
    redwoodHost = os.getenv('REDWOOD_HOST', 'ucsc-cgp.org')
    if name == 'file_browser':
        return render_template(name + '.html', data=data)
    if name == 'invoicing_service' or name == 'invoicing_service1':
        return redirect(url_for('invoicing_service'))
    if name == 'action_service':
        return redirect(url_for('action_service'))
    if name == 'help':
        return render_template(name+'.html',
                               coreClientVersion=coreClientVersion,
                               redwoodHost=redwoodHost)
    if name == 'index':
        allJobsQuery = [("regexp", "experimentalStrategy",
                        "[rR][nN][aA][-][Ss][Ee][Qq]"),
                        ("regexp", "software", "[Ss]pinnaker")]
        query_es_rna_seq(es, 'burn_idx', allJobsQuery, "repoDataBundleId")
        return render_template(name + '.html', allJobsQuery=allJobsQuery)
    return render_template(name + '.html')


@app.route('/invoicing_service')
@login_required
def invoicing_service():
    """
    Function for rendering the invoicing page
    """
    data1 = os.environ['DCC_INVOICING_SERVICE']
    return render_template('invoicing_service.html', data=data1)


@app.route('/action_service')
@login_required
def action_service():
    """
    Function to render the action service papge
    """
    data1 = os.environ['DCC_ACTION_SERVICE']
    return render_template('action_service.html', data=data1)


@app.route('/file_browser/')
def html_rend_file_browser():
    """
    Helper method to redirect URLs ending in <url>/file_browser/
    to the file browser page.
    """
    return redirect(url_for('html_rend', name='file_browser'))


@app.route('/token')
def token():
    """
    Endpoint to request a token
    """
    if current_user.is_authenticated:
        # this is where I would retrieve the token, encode it, pass it along.
        token = current_user.redwood_token
        return Response(token, mimetype='text/plain',
                        headers={"Content-disposition":
                                 "attachment; filename=token.txt"})
    else:
        return redirect(url_for('login'))


@app.route('/login')
def login():
    """
    Endpoint to Login into the page
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    google = get_google_auth()
    auth_url, state = google.authorization_url(
        Auth.AUTH_URI, access_type='offline',
        prompt='select_account consent')
    session['oauth_state'] = state
    return redirect(auth_url)


@app.route('/gCallback')
def callback():
    """
    Callback method required by Google's OAuth 2.0
    """
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('index'))
    if 'error' in request.args:
        if request.args.get('error') == 'access_denied':
            return 'You denied access.'
        return 'Error encountered.'
    if 'code' not in request.args and 'state' not in request.args:
        return redirect(url_for('login'))
    else:
        google = get_google_auth(state=session['oauth_state'])
        try:
            token = google.fetch_token(
                Auth.TOKEN_URI,
                client_secret=Auth.CLIENT_SECRET,
                authorization_response=request.url)
        except HTTPError:
            return 'HTTPError occurred.'
        # Testing the token verification step.
        try:
            # jwt = verify_id_token(token['id_token'], Auth.CLIENT_ID)
            verify_id_token(token['id_token'], Auth.CLIENT_ID)
        except AppIdentityError:
            return 'Could not verify token.'
        # Check if you have the appropriate domain
        # Commenting this section out to let anyone with
        # a google account log in.
        # if 'hd' not in jwt or jwt['hd'] != 'ucsc.edu':
        #     flash('You must login with a ucsc.edu account. \
        #            Please try again.', 'error')
        #     return redirect(url_for('index'))

        google = get_google_auth(token=token)
        resp = google.get(Auth.USER_INFO)
        if resp.status_code == 200:
            user_data = resp.json()
            email = user_data['email']
            user = User.query.filter_by(email=email).first()
            if user is None:
                user = User()
                user.email = email
            user.name = user_data['name']
            print(token)
            user.tokens = json.dumps(token)
            user.access_token = token['access_token']
            user.avatar = user_data['picture']
            user.redwood_token = get_redwood_token(user)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            # Empty flashed messages
            get_flashed_messages()
            # Set a new success flash message
            flash('You are now logged in!', 'success')
            return redirect(url_for('index'))
        return 'Could not fetch your information.'


def get_redwood_token(user):
    """
    Helper method to fetch the token from
    Redwood.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    username = os.environ['REDWOOD_ADMIN']
    password = os.environ['REDWOOD_ADMIN_PASSWORD']
    server = os.environ['REDWOOD_SERVER']
    server_port = os.environ['REDWOOD_ADMIN_PORT']
    url = "https://{}:{}@{}:{}/users/{}/tokens".format(username,
                                                       password,
                                                       server,
                                                       server_port,
                                                       user.email)
    # json_str = urlopen(str("https://"+username+":
    # "+password+"@"+server+":"+server_port+"/users/
    # "+user.email+"/tokens"), context=ctx).read()
    json_str = urlopen(url, context=ctx).read()
    try:
        json_struct = json.loads(json_str)
        token_str = json_struct['tokens'][0]['access_token']
        return token_str
    except Exception:
        print 'Exception getting token'
    return 'None'


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
