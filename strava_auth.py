import os
import requests
from swagger_client.swagger_client.configuration import Configuration

config = Configuration()

def update_env_file(key, value):
    """Update a value in the .env file"""
    env_path = '.env'
    
    with open(env_path, 'r') as file:
        lines = file.readlines()
    
    key_found = False
    for i, line in enumerate(lines):
        if line.startswith(f'{key}='):
            lines[i] = f'{key}={value}\n'
            key_found = True
            break
    
    if not key_found:
        lines.append(f'{key}={value}\n')
    
    with open(env_path, 'w') as file:
        file.writelines(lines)

def get_valid_access_token():
    """Get a valid access token, refreshing if necessary"""
    refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
    )
    
    if response.status_code == 200:
        token_data = response.json()
        new_access_token = token_data['access_token']
        new_refresh_token = token_data['refresh_token']
        
        update_env_file('STRAVA_ACCESS_TOKEN', new_access_token)
        update_env_file('STRAVA_REFRESH_TOKEN', new_refresh_token)
        
        os.environ['STRAVA_ACCESS_TOKEN'] = new_access_token
        os.environ['STRAVA_REFRESH_TOKEN'] = new_refresh_token
        
        print("✓ Tokens refreshed and saved to .env file")
        
        return new_access_token
    else:
        raise Exception(f"Failed to refresh token: {response.text}")

def configure_strava_client():
    """Configure the Swagger client with a valid access token"""
    config.access_token = get_valid_access_token()
    return config