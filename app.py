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

@app.route('/activities')
def activities():
    all_activities = Activity.query.order_by(Activity.start_date_local.desc()).all()
    
    total_distance = sum(a.distance for a in all_activities) / 1000  # km
    total_runs = len(all_activities)
    
    return render_template('activities.html', 
                         activities=all_activities,
                         total_distance=round(total_distance, 2),
                         total_runs=total_runs)

@app.route('/activity/<int:activity_id>')
def activity_detail(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    return render_template('activity_detail.html', activity=activity)

@app.route('/')
def stats():
    activities = Activity.query.all()
    
    if not activities:
        return render_template('stats.html', stats=None)
    
    total_distance = sum(a.distance for a in activities) / 1000  
    total_time = sum(a.moving_time for a in activities) / 3600  
    total_elevation = sum(a.total_elevation_gain or 0 for a in activities)
    total_runs = len(activities)
    
    avg_distance = total_distance / total_runs if total_runs > 0 else 0
    avg_pace = (total_time * 60) / total_distance if total_distance > 0 else 0  
    
    activity_types = {}
    for a in activities:
        activity_types[a.type] = activity_types.get(a.type, 0) + 1
    
    recent_activities = Activity.query.order_by(Activity.start_date_local.desc()).limit(10).all()
    
    from collections import defaultdict
    monthly_stats = defaultdict(lambda: {'distance': 0, 'count': 0, 'time': 0})
    
    for a in activities:
        month_key = a.start_date_local.strftime('%Y-%m')
        monthly_stats[month_key]['distance'] += a.distance / 1000
        monthly_stats[month_key]['count'] += 1
        monthly_stats[month_key]['time'] += a.moving_time / 3600
    
    stats = {
        'total_distance': round(total_distance, 2),
        'total_time': round(total_time, 2),
        'total_elevation': total_elevation,
        'total_runs': total_runs,
        'avg_distance': round(avg_distance, 2),
        'avg_pace': round(avg_pace, 2),
        'activity_types': activity_types,
        'recent_activities': recent_activities,
        'monthly_stats': dict(sorted(monthly_stats.items(), reverse=True))
    }

    return render_template('index.html', stats=stats)

@app.route('/sync_activities')
def sync_activities():
    try:
        from strava_auth import configure_strava_client
        from swagger_client.swagger_client import api_client
        
        config = configure_strava_client()
        
        api_client_instance = api_client.ApiClient(config)
        
        api_instance = swagger_client.swagger_client.ActivitiesApi(api_client_instance)
        
        print(f"Using token: {config.access_token[:20]}...")
        
        strava_activities = api_instance.get_logged_in_athlete_activities(per_page=200)
        
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