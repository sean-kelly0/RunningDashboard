from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import swagger_client
from swagger_client.swagger_client.rest import ApiException
from pprint import pprint
from dotenv import load_dotenv
import os
import requests
from strava_auth import configure_strava_client


load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Activity(db.Model):
    __tablename__ = 'activity'

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
    try:
        from strava_auth import configure_strava_client
        from swagger_client.swagger_client import api_client
        
        config = configure_strava_client()
        
        api_client_instance = api_client.ApiClient(config)
        
        api_instance = swagger_client.swagger_client.ActivitiesApi(api_client_instance)
        
        print(f"Using token: {config.access_token[:20]}...")
        
        strava_activities = api_instance.get_logged_in_athlete_activities(per_page=30)
        
        activities_added = 0
        
        for strava_activity in strava_activities:
            existing = Activity.query.filter_by(id=strava_activity.id).first()
            
            if not existing:
                activity = Activity(
                    id=strava_activity.id,
                    name=strava_activity.name,
                    description=getattr(strava_activity, 'description', None) or '',
                    distance=int(strava_activity.distance),
                    moving_time=strava_activity.moving_time,
                    type=strava_activity.type,
                    total_elevation_gain=int(getattr(strava_activity, 'total_elevation_gain', 0) or 0),
                    start_date_local=strava_activity.start_date_local,
                    city=getattr(strava_activity, 'city', None),
                    state=getattr(strava_activity, 'state', None),
                    country=getattr(strava_activity, 'country', None),
                    device_name=getattr(strava_activity, 'device_name', None)
                )
                
                db.session.add(activity)
                activities_added += 1
        
        db.session.commit()
        
        return f"Successfully synced! Added {activities_added} new activities."
        
    except swagger_client.swagger_client.rest.ApiException as e:
        return f"Error fetching activities: {e}"
    except Exception as e:
        db.session.rollback()
        return f"Error saving to database: {e}"

@app.route('/exchange_token')
def exchange_token():
    code = request.args.get('code')
    
    if not code:
        return "Error: No authorization code provided"
    
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
    
    if 'errors' in token_data or 'access_token' not in token_data:
        print(f"Error from Strava: {token_data}")
        return f"Error: {token_data.get('message', 'Failed to exchange token')}"
    
    access_token = token_data['access_token']
    refresh_token = token_data['refresh_token']
    
    from strava_auth import update_env_file
    
    update_env_file('STRAVA_ACCESS_TOKEN', access_token)
    update_env_file('STRAVA_REFRESH_TOKEN', refresh_token)
    
    print(f"✓ Tokens saved to .env file")
    print(f"Access Token: {access_token}")
    print(f"Refresh Token: {refresh_token}")
    
    return "Token received and saved to .env file! You're all set."

if __name__ == '__main__':
    app.run(debug=True)