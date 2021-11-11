# import flask stuff 

from flask import Flask, render_template, url_for

app = Flask(__name__)

import data

@app.route('/')
@app.route('/index')
def index():
    episode_data = data.get_episode_data()
    return render_template('index.html', episode_data=episode_data)

app.run(debug=True)