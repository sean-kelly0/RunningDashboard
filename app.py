from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

swagger_client.configuration.access_token = os.getenv('STRAVA_ACCESS_TOKEN')

api_instance = swagger_client.ActivitiesApi()

try:
    activities = api_instance.get_logged_in_athlete_activities()
    for activity in activities:
        print(activity.name, activity.distance)
except ApiException as e:
    print(f"Exception: {e}")

class Activity(db.Model):
    table_name = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    distance = db.Column(db.Integer, nullable=False)
    moving_time = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    total_elevation_gain = db.Column(db.Integer, nullable=True)
    start_date_local = db.Column(db.DateTime, nullable=False)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    device_name = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<Activity {self.name}>'
    


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)