from flask import Flask, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
from flask import render_template, flash, Markup
from flask import session
from flask_pymongo import PyMongo

from github import Github

import pprint
import os
import sys
import traceback
import time


class GithubOAuthVarsNotDefined(Exception):
    '''raise this if the necessary env variables are not defined '''

if os.getenv('GITHUB_CLIENT_ID') == None or \
        os.getenv('GITHUB_CLIENT_SECRET') == None or \
        os.getenv('APP_SECRET_KEY') == None or \
        os.getenv('GITHUB_ORG') == None:
    raise GithubOAuthVarsNotDefined('''
      Please define environment variables:
         GITHUB_CLIENT_ID
         GITHUB_CLIENT_SECRET
         GITHUB_ORG
         APP_SECRET_KEY
      ''')

app = Flask(__name__)

app.debug = False

app.secret_key = os.environ['APP_SECRET_KEY']
oauth = OAuth(app)


github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'],
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],
    request_token_params={'scope': 'read:org'},
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize'
)
app.config['MONGO_HOST'] = os.environ['MONGO_HOST']
app.config['MONGO_PORT'] = int(os.environ['MONGO_PORT'])
app.config['MONGO_DBNAME'] = os.environ['MONGO_DBNAME']
app.config['MONGO_USERNAME'] = os.environ['MONGO_USERNAME']
app.config['MONGO_PASSWORD'] = os.environ['MONGO_PASSWORD']
mongo = PyMongo(app)
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

@app.context_processor
def inject_logged_in():
    return dict(logged_in=('github_token' in session))

@app.context_processor
def inject_github_org():
    return dict(github_org=os.getenv('GITHUB_ORG'))

app.secret_key='w98fw9ef8hwe98fhwef'
#session.clear()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You were logged out')
    return redirect(url_for('home'))

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()

    if resp is None:
        session.clear()
        login_error_message = 'Access denied: reason=%s error=%s full=%s' % (
            request.args['error'],
            request.args['error_description'],
            pprint.pformat(request.args)
        )        
        flash(login_error_message, 'error')
        return redirect(url_for('home'))    

    try:
        session['github_token'] = (resp['access_token'], '')
        session['user_data']=github.get('user').data
        github_userid = session['user_data']['login']
        org_name = os.getenv('GITHUB_ORG')
    except Exception as e:
        session.clear()
        message = 'Unable to login: ' + str(type(e)) + str(e)
        flash(message,'error')
        return redirect(url_for('home'))
    
    try:
        g = Github(resp['access_token'])
        org = g.get_organization(org_name)
        named_user = g.get_user(github_userid)
        isMember = org.has_in_members(named_user)
    except Exception as e:
        message = 'Unable to connect to Github with accessToken: ' + resp['access_token'] + " exception info: " + str(type(e)) + str(e)
        session.clear()
        flash(message,'error')
        return redirect(url_for('home'))
    
    if not isMember:
        session.clear() # Must clear session before adding flash message
        message = 'Unable to login: ' + github_userid + ' is not a member of ' + org_name + \
          '</p><p><a href="https://github.com/logout" target="_blank">Logout of github as user:  ' + github_userid + \
          '</a></p>' 
        flash(Markup(message),'error')

    else:
        flash('You were successfully logged in')

    return redirect(url_for('home'))    

@app.route('/map')
def render_map():	
		l1_result = []
		l2_result = []
		title_result = []
		time_result = []
		date_result = []
		etype_result = []
		location_result = []
		for document in mongo.db.events.find():
			l1_result.append(document["N/S Coordinate"])
			l2_result.append(document["E/W Coordinate"])
			title_result.append(document["Name"])
			time_result.append(document["Time"])
			date_result.append(document["Date"])
			etype_result.append(document["Type"])
			location_result.append(document["Location"])
		return render_template('map.html', l1 = l1_result, l2 = l2_result, title = title_result, time = time_result, date = date_result, etype = etype_result, location = location_result)

@app.route('/pin')
def render_pin():
    return render_template('pin.html')

@app.route('/about')
def render_about():
    return render_template('about.html')

@app.route('/pin_result')
def render_pin_result():
	try:
		title_result = str(request.args['title'])
		date_result = str(request.args['month'] + " " + request.args['day'] +  ", " + request.args['year'])
		time_result = str(request.args['time'] +  " " + request.args['ampm'])
		etype_result = str(request.args['etype'])
		location_result = str(request.args['location'])
		location1_result = float(request.args['location1'])
		location2_result = float(request.args['location2'])
		session['title']=title_result
		session['date']=date_result
		session['time']=time_result
		session['etype']=etype_result
		session['location']=location_result
		session['location1']=location1_result
		session['location2']=location2_result
		dat_result = time.asctime( time.localtime(time.time()) )
		mongo.db.events.insert_one( {"Name": title_result, "Type": etype_result, "Date": date_result, "Time": time_result, "Location": location_result, "N/S Coordinate": location1_result, "E/W Coordinate": location2_result})
		return render_template('pin_result.html',  title=title_result, date=date_result, time=time_result, etype=etype_result, location=location_result, location1=location1_result, location2=location2_result, dat=dat_result)
	except ValueError:
		return "Sorry: something went wrong."



if __name__=="__main__":
    app.run(debug=False, port=5000)
