import os
import json
import datetime

from flask import Flask, url_for, redirect, \
    render_template, session, request, Response, \
    flash, get_flashed_messages, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin
from oauthlib.oauth2 import OAuth2Error

from decode_cookie import decodeFlaskCookie
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from models import get_all
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError
from oauth2client.client import verify_id_token
from oauth2client.crypt import AppIdentityError


import ssl
from urllib import urlencode, urlopen
import urllib2

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
    GOOGLE_SITE_VERIFICATION_CODE = os.environ.get("GOOGLE_SITE_VERIFICATION_CODE") or ""


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


""" DB Models """


class User(db.Model, UserMixin):
    __tablename__ = "users"
    email = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(200))
    refresh_token = db.Column(db.String(5000))
    tokens = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    def get_id(self):
        return self.email


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


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
    """Returns the cardinality based from the inputs
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
    es_object -- the es object to query against
    index -- the name of the index to query on
    query_params -- tuple with form (query type, field, value)
    cardinality -- field to get the cardinality from
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


@app.route('/')
def index():
    """
    Render the main page.
    """
    return html_rend('index')


def parse_token():
    """
    Parses the Authorization token from the request header
    :return: the bearer and token string
    """
    authorization_header = request.headers.get("Authorization", None)
    assert authorization_header is not None, "No Authorization header in the request"
    parts = authorization_header.split()
    # Return the bearer and token string
    return parts[0], parts[1]

def get_logged_user(cookie):
    decoded_cookie = decodeFlaskCookie(os.getenv('SECRET_KEY', 'somethingsecret'), cookie)
    assert (decoded_cookie.viewkeys()
            >= {'user_id', '_fresh'}), "Cookie not valid; does not have necessary fields"
    assert (User.query.get(decoded_cookie['user_id']) is not None), "No user with {}".format(
        decoded_cookie['user_id'])
    logged_user = User.query.get(decoded_cookie['user_id'])
    return logged_user

def new_google_access_token(request):
    cookie = request.cookies.get('session')
    logged_user = get_logged_user(cookie)
    refresh_token = logged_user.refresh_token
    oauth = get_google_auth()
    extra = {
        'client_id': Auth.CLIENT_ID,
        'client_secret': Auth.CLIENT_SECRET,
    }
    resp = oauth.refresh_token(Auth.TOKEN_URI, refresh_token=refresh_token, **extra)
    return resp['access_token']

def make_request(url, headers):
    try:
        req = urllib2.Request(url, headers=headers)
        handler = urllib2.urlopen(req)
        content_type = handler.headers['content-type']
        response = Response(handler.read(), mimetype=content_type)
        content_encoding = 'content-encoding'
        if content_encoding in handler.headers.keys():
            response.headers[content_encoding] = handler.headers[
                content_encoding]
        return response
    except urllib2.HTTPError as e:
        return e.message, e.code

@app.route('/check_session/<cookie>')
def check_session(cookie):
    if not request.headers.get("Authorization", None):
        return jsonify({"error": "No Authorization header in the request"})
    else:
        # Make sure the auth token is the right one
        try:
            bearer, auth_token = parse_token()
            assert bearer == "Bearer", "Authorization must start with Bearer"
            assert auth_token == os.getenv("LOG_IN_TOKEN", 'ITS_A_SECRET!')
        except AssertionError as e:
            response = {
                'error': e.message
            }
            return jsonify(response)
        try:
            logged_user = get_logged_user(cookie)
            response = {
                'email': logged_user.email,
                'name': logged_user.name,
                'avatar': logged_user.avatar
            }
        except AssertionError as e:
            response = {
                'error': e.message
            }
        return jsonify(response)


@app.route('/export_to_firecloud')
@login_required
def export_to_firecloud():
    """
    Creates and returns a manifest based on the filters pased on
    to this endpoint
    parameters:
        - name: filters
          in: query
          type: string
          description: Filters to be applied when generating the manifest
        - name: workspace
          in: query
          type: string
          description: The name of the FireCloud workspace to create
        - name: namespace
          in: query
          type: string
          description: The namespace of the FireCloud workspace to create
    :return:
    """
    workspace = request.args.get('workspace');
    if workspace is None:
        return "Missing workspace query parameter", 400
    namespace = request.args.get('namespace')
    if namespace is None:
        return "Missing namespace query parameter", 400
    # filters are optional
    filters = request.args.get('filters')
    try:
        access_token = new_google_access_token(request)
    except OAuth2Error as e:
        return "Error getting access token", 401
    params = urlencode(
        {'workspace': workspace, 'namespace': namespace, 'filters': filters})
    url = "{}://{}/repository/files/export/firecloud?{}".format(
        os.getenv('DCC_DASHBOARD_PROTOCOL'),
        os.getenv('DCC_DASHBOARD_HOST'), params)
    headers = {'Authorization': "Bearer {}".format(access_token)}
    return make_request(url, headers)

@app.route('/proxy_firecloud', methods=['GET'])
@login_required
def proxy_firecloud():
    path = request.args.get('path')
    if path is None:
        return "Missing path query parameter", 400
    pathParam = path if path.startswith('/') else '/' + path
    try:
        access_token = new_google_access_token(request)
    except OAuth2Error as e:
        return "Error getting access token", 401
    url = "{}{}".format(os.getenv('FIRECLOUD_API_BASE', 'https://api.firecloud.org'), pathParam)
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    for header in ['Accept', 'Accept-Language', 'Accept-Encoding']:
        val = request.headers[header]
        if val is not None:
            headers[header] = val
    return make_request(url, headers)

@app.route('/<name>.html')
def html_rend(name):
    """
    Render templates based on their name.
    Handle the templates differently depending
    on its name.
    """
    data = os.environ['DCC_DASHBOARD_SERVICE']
    coreClientVersion = os.getenv('DCC_CORE_CLIENT_VERSION', '1.1.0')
    if name == 'file_browser':
        return render_template(name + '.html', data=data)
    if name == 'invoicing_service' or name == 'invoicing_service1':
        return redirect(url_for('invoicing_service'))
    if name == 'action_service':
        return redirect(url_for('action_service'))
    if name == 'help':
        return render_template(name+'.html',
                               coreClientVersion=coreClientVersion)
    if name == 'index':
        return render_template(name + '.html')
    if name == 'boardwalk':
        return boardwalk()
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


@app.route('/boardwalk')
def boardwalk():
    return redirect(url_for('boardwalk'))

@app.route('/privacy')
def privacy():
    return redirect(url_for('privacy'))


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
            user.refresh_token = token['refresh_token']
            user.avatar = user_data['picture']
            db.session.add(user)
            db.session.commit()
            login_user(user)
            # Empty flashed messages
            get_flashed_messages()
            # Set a new success flash message
            flash('You are now logged in!', 'success')
            return redirect(url_for('index'))
        return 'Could not fetch your information.'


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
