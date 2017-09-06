from __future__ import print_function
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
from datetime import datetime
import pytz
from pytz import timezone

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
        session.clear()
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
		stime_result = []
		etime_result = []
		capacity_result = []
		date_result = []
		etype_result = []
		location_result = []
		mon_result = []
		day_result = []
		year_result = []
		for document in mongo.db.events.find():
			l1_result.append(document["N/S Coordinate"])
			l2_result.append(document["E/W Coordinate"])
			title_result.append(document["Name"])
			stime_result.append(document["Start Time"])
			etime_result.append(document["End Time"])
			capacity_result.append(document["Capacity"])
			date_result.append(document["Date"])
			etype_result.append(document["Type"])
			location_result.append(document["Location"])
			mon_result.append(document["Month"])
			day_result.append(document["Day"])
			year_result.append(document["Year"])
		return render_template('map.html', l1 = l1_result, l2 = l2_result, title = title_result, stime = stime_result, etime = etime_result, date = date_result, etype = etype_result, location = location_result, capacity = capacity_result, mon = mon_result, day = day_result, year=year_result)

@app.route('/pin')
def render_pin():
    return render_template('pin.html')

@app.route('/about')
def render_about():
    return render_template('about.html')

@app.route('/rsvp')
def render_rsvp():
	name = str(request.args['eventtitle'])
	document = mongo.db.events.find_one({ 'Name': name })
	l1_result = document["N/S Coordinate"]
	l2_result = document["E/W Coordinate"]
	stime_result = document["Start Time"]
	etime_result = document["End Time"]
	capacity_result = document["Capacity"]
	date_result = document["Date"]
	etype_result = document["Type"]
	location_result = document["Location"]
	mon_result = document["Month"]
	day_result = document["Day"]
	year_result = document["Year"]
	return render_template('rsvp.html', l1 = l1_result, l2 = l2_result, stime = stime_result, etime = etime_result, date = date_result, etype = etype_result, location = location_result, capacity = capacity_result, mon = mon_result, day = day_result, year=year_result, title = name)

@app.route('/pin_result')
def render_pin_result():
	try:
		title_result = str(request.args['title'])
		day_result = int(request.args['day'])
		month_result = int(request.args['month'])
		if (month_result == 1):
			mon = "January" 
		if (month_result == 2):
			mon = "February" 
		if (month_result == 3):
			mon = "March" 
		if (month_result == 4):
			mon = "April" 
		if (month_result == 5):
			mon = "May" 
		if (month_result == 6):
			mon = "June" 
		if (month_result == 7):
			mon = "July" 
		if (month_result == 8):
			mon = "August" 
		if (month_result == 9):
			mon = "September" 
		if (month_result == 10):
			mon = "October" 
		if (month_result == 11):
			mon = "November" 
		if (month_result == 12):
			mon = "December" 
		year_result = int(request.args['year'])
		date_result = str(request.args['month'] + " " + request.args['day'] +  ", " + request.args['year'])
		stime_result = int(request.args['stime'])
		etime_result = int(request.args['etime'])
		etype_result = str(request.args['etype'])
		capacity_result = int(request.args['capacity'])
		location_result = str(request.args['location'])
		location1_result = float(request.args['location1'])
		location2_result = float(request.args['location2'])
		dat_result = time.asctime( time.localtime(time.time()) )
		session['title'] = title_result
		session['month'] = month_result
		session['day'] = day_result
		session['year'] = year_result
		session['date'] = date_result
		session['stime'] = stime_result
		session['etime'] = etime_result
		session['etype'] = etype_result
		session['capacity'] = capacity_result
		session['location'] = location_result
		session['location1'] = location1_result
		session['location2'] = location2_result
		pacific = pytz.timezone('America/Los_Angeles')
		ts = datetime(year_result,month_result,day_result,etime_result,0,0,0, tzinfo=pacific)
		ts2 = pacific.localize(datetime(year_result,month_result,day_result,etime_result,0,0,0))
		pytz.utc.normalize(ts)
		pytz.utc.normalize(ts2)
		print (ts,file=sys.stderr)
		utc = ts.astimezone(timezone('UTC'))
		print (utc,file=sys.stderr)
		mongo.db.events.create_index("expiress", expireAfterSeconds=int(0))
		mongo.db.events.insert_one( {"Name": title_result, "Type": etype_result, "Date": date_result, "Start Time": stime_result, "End Time": etime_result, "Capacity": capacity_result, "Location": location_result, "N/S Coordinate": location1_result, "E/W Coordinate": location2_result, "expiress": ts2, "Month": mon, "Day": day_result, "Year": year_result} )
		return render_template('pin_result.html',  title=title_result, date=date_result, stime=stime_result, etime=etime_result, etype=etype_result, location=location_result, location1=location1_result, location2=location2_result, dat=dat_result, capacity = capacity_result, mon = mon, day = day_result)
	except ValueError:
		return "Sorry: something went wrong."



if __name__=="__main__":
    app.run(debug=False, port=54322)
