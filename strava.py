import requests
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import os
import time
import math
from datetime import datetime

FIELDS = ['id', 'name', 'distance', 'moving_time', 'elapsed_time', 'total_elevation_gain', 'type', 
'start_date_local', 'achievement_count', 'kudos_count', 'start_latlng', 'average_speed', 'max_speed', 'average_cadence', 
'average_watts', 'max_watts', 'weighted_average_watts', 'kilojoules', 'device_watts', 'has_heartrate', 
'average_heartrate', 'max_heartrate', 'elev_high', 'elev_low', 'pr_count', 'suffer_score']

# Load environment variables
load_dotenv()

class Strava:
    def __init__(self):
        self.client_id = os.getenv('CLIENT_ID')
        self.secret = os.getenv('CLIENT_SECRET')
        self.baseUrl = "https://www.strava.com"

        #self.access = "a470721ed05d45684b7ead9a969d782f8f9a0f46"
        #self.refresh = "1134629d6b7dbc1e879d1c9b91614d27a15227b3"
        
        #self.expires_at = 0
        
        #self.access_root = "4fbfcf70fd18ba464357939fbde5b8e182278772"
        #self.refresh_root = "0f2cd0013ad5975e83a72b5f877ac2bbb8798a55"
        
        self.activities = []
        self.activities_summ = []

    def authenticate(self):

        # This information is obtained upon registration of a new GitHub
        client_id = self.client_id
        client_secret = self.secret
        auth_base_url = 'https://www.strava.com/oauth/authorize'
        redirect_url = 'http://127.0.0.1:5000/authorise'
        scope = ["profile:read_all,read_all,activity:read_all"]

        # Create session variable
        session = OAuth2Session(client_id=client_id, redirect_uri=redirect_url, scope = scope)

        # Get auth link
        auth_link = session.authorization_url(auth_base_url)

        return auth_link[0]

    def exchange(self, code):

        # Get url
        url = f"{self.baseUrl}/oauth/token"

        # Set payload
        payload = {
            "client_id": self.client_id,
            "client_secret": self.secret,
            "code": code
        }

        # Submit for requests
        r = requests.post(url, payload)

        # Check for status
        if r.status_code != 200:
            print("Request to refresh access token failed with error code " + str(r.status_code))
            return []
        
        # Output results and reassign
        results = r.json()

        # Store access token
        access_token = results['access_token']
        refresh_token = results['refresh_token']

        # TODO: WE can get name of the user and profile photo from these results
    
        return results

    def refresh_key(self):

        url = f"{self.baseUrl}/oauth/token"

        payload = {
            "client_id": self.client_id,
            "client_secret": self.secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh
        }

        r = requests.post(url, payload)

        # Check for status
        if r.status_code != 200:
            print("Request to refresh access token failed with error code " + str(r.status_code))
            return []
        
        # Output results and reassign
        results = r.json()
        self.access = results['access_token']
        self.expires_at = results['expires_at']        

    def get_activities_new(self, page, creds):

            # Get URL
            url = f"{self.baseUrl}/api/v3/athlete/activities"

            # Check if previous access key had expired, and if so request another
            #if time.time() > self.expires_at:
            #    self.refresh_key()

            # Set header
            params = {"per_page": 200, "page":page + 1}
            headers = {"Authorization": f"Bearer {creds['access_key']}"}
            r = requests.get(url, params = params, headers = headers)

            # Check for status
            if r.status_code != 200:
                err_message = f"Request to Strava API failed with error code {str(r.status_code)}"
                raise Exception(err_message)
            
            # Get results for required fields
            raw = r.json()
            results = [{key:row.get(key, 'n/a') for key in FIELDS} for row in raw]
            return self.calculated_fields(results)


    def get_activities(self, page, creds=[]):

        # Get URL
        url = f"{self.baseUrl}/api/v3/athlete/activities"

        # Check if previous access key had expired, and if so request another
        if time.time() > self.expires_at:
            self.refresh_key()

        # Set header
        params = {"per_page": 200, "page":page + 1}
        headers = {"Authorization": f"Bearer {self.access}"}
        r = requests.get(url, params = params, headers = headers)

        # Check for status
        if r.status_code != 200:
            err_message = f"Request to Strava API failed with error code {str(r.status_code)}"
            raise Exception(err_message)
        
        # Get results for required fields
        raw = r.json()
        results = [{key:row.get(key, 'n/a') for key in FIELDS} for row in raw]
        return self.calculated_fields(results)

    def calculated_fields(self, results):

        if results == []:
            print("No activities found")
            return

        # For each activity, format existing rows and add new calculated fields
        for row in results:

            # Format start date
            date = datetime.strptime(row['start_date_local'][:10], "%Y-%m-%d")
            row['date'] = date.strftime("%d/%m/%Y")
            row['date_sort'] = date.toordinal()
            row['time'] = row['start_date_local'][11:-1]
            row.pop('start_date_local')

            # Format distance in km
            row['distance_f'] = f"{(row['distance']/1000):.02f}km"

            # Get time formatted
            hours = math.floor(row["moving_time"] / (3600))
            minutes = math.floor((row["moving_time"] - hours * 3600) / 60)
            seconds = round(row['moving_time'] % 60)
            row['moving_time_f'] = f"{hours:02}:{minutes:02}:{seconds:02}"

            # Get pace - kph for rides, and time per km for runs and walks
            if row["type"] == 'Ride':
                speed = row['average_speed'] * 3.6
                row["pace"] = f"{speed:.1f}km/h"
            else:
                sec_per_km = 1000 / row['average_speed']
                minutes = math.floor(sec_per_km / 60)
                seconds = round(sec_per_km % 60)
                row['pace'] = f"{minutes:02}:{seconds:02}/km"

            # Reformat average heart rate 
            if row['has_heartrate']:
                row['average_heartrate_sort'] = float(row['average_heartrate'])
                row['max_heartrate_sort'] = float(row['max_heartrate'])
            else:
                row['average_heartrate_sort'] = 0  
                row['max_heartrate_sort'] = 0

            # Unpack start and end co-ordinates
            if len(row.get('start_latlng', [])) == 2:
                row['start_lat'] = row['start_latlng'][0]
                row['start_lng'] = row['start_latlng'][1]
            else:
                row['start_lat'] = "n/a"
                row['start_lng'] = "n/a"
            row.pop('start_latlng')
        
        return results





#strava = Strava()
#out = strava.get_activities(0)


fields_all = ['resource_state', 'athlete', 'name', 'distance', 'moving_time', 
'elapsed_time', 'total_elevation_gain', 'type', 'sport_type', 'workout_type', 
'id', 'start_date', 'start_date_local', 'timezone', 'utc_offset', 
'location_city', 'location_state', 'location_country', 'achievement_count', 
'kudos_count', 'comment_count', 'athlete_count', 'photo_count', 'map', 'trainer', 
'commute', 'manual', 'private', 'visibility', 'flagged', 'gear_id', 'start_latlng', 
'end_latlng', 'average_speed', 'max_speed', 'average_cadence', 'average_watts', 'max_watts', 
'weighted_average_watts', 'kilojoules', 'device_watts', 'has_heartrate', 'average_heartrate', 
'max_heartrate', 'heartrate_opt_out', 'display_hide_heartrate_option', 'elev_high', 'elev_low', 
'upload_id', 'upload_id_str', 'external_id', 'from_accepted_tag', 'pr_count', 'total_photo_count', 
'has_kudoed', 'suffer_score']
