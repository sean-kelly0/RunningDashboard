from flask import Flask, render_template, url_for
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

app = Flask(__name__)

# Configure OAuth2 access token for authorization: strava_oauth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.ActivitiesApi()
id = 789 # Long | The identifier of the activity.
includeAllEfforts = true # Boolean | To include all segments efforts. (optional)

try: 
    # Get Activity
    api_response = api_instance.getActivityById(id, includeAllEfforts=includeAllEfforts)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ActivitiesApi->getActivityById: %s\n" % e)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)