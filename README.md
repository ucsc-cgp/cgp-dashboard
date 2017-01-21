# dcc-dashboard
The Core's web dashboard including a faceted file browser

This iteration of the File Browser uses the web API from https://github.com/BD2KGenomics/dcc-dashboard-service

## Set up the web API
Follow the directions on https://github.com/BD2KGenomics/dcc-dashboard-service.

## Locally run the Dashboard
Create a local host

      python -m SimpleHTTPServer 8080

Open index.html on a web browser, click on File Browser
If results are not showing, be sure to allow CORS (cross-origin-resource-sharing)

## Setup

    virtualenv env
    source env/bin/activate
    pip install --upgrade pip
    pip install -r ./requirements.txt

See http://bitwiser.in/2015/09/09/add-google-login-in-flask.html

Within python session:

    from app import db
    db.create_all()
    from werkzeug.serving import make_ssl_devcert
    make_ssl_devcert('./ssl', host='localhost')

Run it:

    python run.py
