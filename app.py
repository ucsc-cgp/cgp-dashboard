import os

from flask import Flask, url_for, redirect, \
    render_template, session, request, Response, \
    flash, get_flashed_messages, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin
from oauthlib.oauth2 import OAuth2Error

from elasticsearch_dsl import Search
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError
from oauth2client.client import verify_id_token
from oauth2client.crypt import AppIdentityError


from urllib import urlencode
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
    SCOPE = ['https://www.googleapis.com/auth/userinfo.profile',
             'https://www.googleapis.com/auth/userinfo.email']


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


class User(UserMixin):

    def __init__(self, user=None, name=None, picture=None):
        """
        Pulls the user's info from the session. We use @property to keep the
        session as the one source of truth, but allow access and setting of
        user properties here.
        """
        if user is not None:
            session['email'] = user
        if name is not None:
            session['name'] = name
        if picture is not None:
            session['avatar'] = picture
        # self._created_at = session.get('created_at', datetime.datetime.utcnow())

    @property
    def email(self):
        return session.get('email', None)

    @email.setter
    def email(self, value):
        session['email'] = value

    @property
    def name(self):
        return session.get('name', None)

    @name.setter
    def name(self, value):
        session['name'] = value

    @property
    def picture(self):
        return session.get('avatar', None)

    @picture.setter
    def picture(self, value):
        session['avatar'] = value

    @property
    def is_active(self):
        return self.email is not None

    @property
    def is_authenticated(self):
        # FIXME: is this right? right to check refresh token?
        return self.refresh_token is not None

    @property
    def is_anonymous(self):
        return self.email is None

    def get_id(self):
        return self.email

    @property
    def tokens(self):
        return session.get('tokens', None)

    @tokens.setter
    def tokens(self, value):
        # Since these tokens won't be encrypted, make sure the refresh
        # token isn't in there
        try:
            del value['refresh_token']
        except KeyError:
            pass
        session['tokens'] = value

    @property
    def refresh_token(self):
        # FIXME: dencrypt
        return session.get('refresh_token', None)

    @refresh_token.setter
    def refresh_token(self, value):
        # FIXME: encrypt
        session['refresh_token'] = value

    def logout(self):
        """Clean up all the stuff we left in the session cookie"""
        for attr in 'email', 'name', 'avatar', 'tokens', 'refresh_token':
            try:
                del session[attr]
            except KeyError:
                pass


@login_manager.user_loader
def load_user(user_id):
    return User()


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


def new_google_access_token():
    refresh_token = current_user.refresh_token
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
        if current_user.email is None:
            response = {
                'error': 'No user is stored in the session. The user is not '
                         'logged in.'
            }
        else:
            response = {
                'email': current_user.email,
                'name': current_user.name,
                'avatar': current_user.picture
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
    workspace = request.args.get('workspace')
    if workspace is None:
        return "Missing workspace query parameter", 400
    namespace = request.args.get('namespace')
    if namespace is None:
        return "Missing namespace query parameter", 400
    # filters are optional
    filters = request.args.get('filters')
    try:
        access_token = new_google_access_token()
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
        access_token = new_google_access_token()
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
    if name == 'unauthorized':
        return render_template(name + '.html')
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
    Function to render the action service page
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

@app.route('/unauthorized')
def unauthorized():
    account = request.args.get('account')
    project = os.getenv('PROJECT_NAME', '')
    contact = os.getenv('CONTACT_EMAIL', '')
    return render_template('unauthorized.html',
        contact=contact, project=project, account=account)


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
            # If so configured, check for whitelist and redirect to
            # unauthorized page if not in whitelist, e.g.,
            # return redirect(url_for('unauthorized', account=<redacted email>)),
            user = User()
            for attr in 'email', 'name', 'picture', 'refresh_token', 'tokens':
                setattr(user, attr, user_data[attr])
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
    User().logout()
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
