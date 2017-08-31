import os
from flask import Flask, url_for, render_template, request


app = Flask(__name__)

@app.route('/')
def render_main():
    return render_template('home.html')

@app.route('/map')
def render_map():
    return render_template('map.html')

@app.route('/pin')
def render_pin():
    return render_template('pin.html')

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
		return render_template('pin_result.html',  title=title_result, month=month_result, day=day_result, year=year_result, time=time_result, ampm=ampm_result, etype=etype_result)
	except ValueError:
		return "Sorry: something went wrong."

if __name__=="__main__":
    app.run(debug=False, port=5000)
