import os
from flask import Flask, url_for, render_template, request

app = Flask(__name__)

@app.route('/')
def render_main():
    return render_template('home.html')

@app.route('/map')
def render_profile():
    return render_template('map.html')

if __name__=="__main__":
    app.run(debug=False, port=5000)
