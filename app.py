from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint
from dotenv import load_dotenv
import os
import requests

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Activity(db.Model):
    __tablename__ = 'activities'

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

@app.route('/activities')
def activities():
    return render_template('activities.html')

@app.route('/sync_activities')
def sync_activities():
    swagger_client.configuration.access_token = os.getenv('STRAVA_ACCESS_TOKEN')
    api_instance = swagger_client.ActivitiesApi()
    
    try:
        # Fetch activities from Strava
        strava_activities = api_instance.get_logged_in_athlete_activities(per_page=30)
        
        activities_added = 0
        
        for strava_activity in strava_activities:
            # Check if activity already exists
            existing = Activity.query.filter_by(id=strava_activity.id).first()
            
            if not existing:
                # Create new activity record
                activity = Activity(
                    id=strava_activity.id,
                    name=strava_activity.name,
                    description=strava_activity.description or '',
                    distance=int(strava_activity.distance),
                    moving_time=strava_activity.moving_time,
                    type=strava_activity.type,
                    total_elevation_gain=int(strava_activity.total_elevation_gain) if strava_activity.total_elevation_gain else 0,
                    start_date_local=strava_activity.start_date_local,
                    device_name=strava_activity.device_name if hasattr(strava_activity, 'device_name') else None
                )
                
                db.session.add(activity)
                activities_added += 1
        
        db.session.commit()
        
        return f"Successfully synced! Added {activities_added} new activities."
        
    except ApiException as e:
        return f"Error fetching activities: {e}"
    except Exception as e:
        db.session.rollback()
        return f"Error saving to database: {e}"

@app.route('/exchange_token')
def exchange_token():
    code = request.args.get('code')
    
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': os.getenv('STRAVA_CLIENT_ID'),
            'client_secret': os.getenv('STRAVA_CLIENT_SECRET'),
            'code': code,
            'grant_type': 'authorization_code'
        }
    )
    
    token_data = response.json()
    print(f"Access Token: {token_data['access_token']}")
    print(f"Refresh Token: {token_data['refresh_token']}")
    
    return "Token received! Check your console and update your .env file"

if __name__ == '__main__':
    app.run(debug=True)