import os
from flask import Flask, url_for, render_template, request
from flask import session
import time




app = Flask(__name__)
app.secret_key='w98fw9ef8hwe98fhwef'
#session.clear()

@app.route('/')
def render_main():
    return render_template('home.html')

@app.route('/map')
def render_map():
		return render_template('map.html')

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
		month_result = str(request.args['month'])
		day_result = int(request.args['day'])
		year_result = int(request.args['year'])
		time_result = str(request.args['time'])
		ampm_result = str(request.args['ampm'])
		etype_result = str(request.args['etype'])
		location_result = str(request.args['location'])
		location1_result = float(request.args['location1'])
		location2_result = float(request.args['location2'])
		session['title']=title_result
		session['month']=month_result
		session['day']=day_result
		session['year']=year_result
		session['time']=time_result
		session['ampm']=ampm_result
		session['location1']=location1_result
		session['location2']=location2_result
		date_result = time.asctime( time.localtime(time.time()) )
		return render_template('pin_result.html',  title=title_result, month=month_result, day=day_result, year=year_result, time=time_result, ampm=ampm_result, etype=etype_result, location=location_result, location1=location1_result, location2=location2_result, date=date_result)
	except ValueError:
		return "Sorry: something went wrong."



if __name__=="__main__":
    app.run(debug=False, port=5000)
