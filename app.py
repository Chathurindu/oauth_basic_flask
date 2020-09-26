import os
import pandas as pd

from flask import Flask, url_for, redirect, session, render_template
from flask_restful import Api, Resource

from authlib.integrations.flask_client import OAuth

from googleapiclient.discovery import build

from functools import wraps

import gspread
from oauth2client.service_account import ServiceAccountCredentials


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        email = dict(session).get('email', None)
        # You would add a check here and usethe user id or something to fetch
        # the other data for that user/check if they exist
        if email:
            return f(*args, **kwargs)
        # return 'You aint logged in, no page for u!'
        return redirect('/login')
    return decorated_function

def login_checked(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        email = dict(session).get('email', None)
        # You would add a check here and usethe user id or something to fetch
        # the other data for that user/check if they exist
        if email:
            return redirect('/home')
        # return 'You aint logged in, no page for u!'
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__, root_path='')
app.secret_key = "random secret"
api = Api(app)

# :) oauth config
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('client_id'),
    client_secret=os.getenv('client_secret'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
)


SAMPLE_SPREADSHEET_ID = os.getenv('SAMPLE_SPREADSHEET_ID')


@app.route('/')
@login_checked
def welcome():
    return render_template('welcome.html')

@app.route('/home')
@login_required
def home():
    email = dict(session).get('email', None)
    # return f'Hello, {email}'
    return render_template('home.html', email= {email})

@app.route('/sheet')
@login_required
def sheet():
    email = dict(session).get('email', None)
    # return f'Hello, {email}'
    return render_template('sheet.html', email= {email})

@app.route('/login')
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    # do something with the token and profile
    session['email'] = user_info['email']
    return redirect('/home')

@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

@app.route('/request-api')
@login_required
def request_api():
    google = oauth.create_client('google')
    redirect_uri = url_for('sheetauth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/sheetauth')
def sheetauth():
    # google_sheet = oauth.create_client('google')
    scope = ['https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(os.getenv('SHEET_NAME')).sheet1
    list_of_hashes = sheet.get_all_records()


    return render_template('sheet.html', msg=list_of_hashes)

records = None
    

class All(Resource):

    def get(self):
        return records

class Name(Resource):

    def get(self, value):
        return [obj for obj in records if obj['first_name'].lower().startswith(value.lower())]

class Email(Resource):

    def get(self, value):
        return [obj for obj in records if obj['email'].lower().startswith(value.lower())]

api.add_resource(All, '/api/')
api.add_resource(Name, '/api/name/<string:value>')
api.add_resource(Email, '/api/email/<string:value>')