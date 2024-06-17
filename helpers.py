from functools import wraps
from flask import redirect, render_template, request, session
from strava import Strava
from requests_oauthlib import OAuth2Session

import sqlite3
from sqlite3 import Error
import re

def apology(error):
    return render_template("apology.html", feedback = error)

def login_required(f):
    """Wrap function to ensure user is logged in to access it"""

    @wraps(f)
    def wrapped_func(* args, ** kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(* args, ** kwargs)

    return wrapped_func


def create_db_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred in connecting to database")

    return connection

def validate_credentials(creds):

    # Check if it is a valid Email
    email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    if not email_pattern.match(creds["email"]):
        return 1

    # Check if it is a valid username
    if len(creds["username"]) < 6:
        return 2
    elif not bool(re.match(r'^(?=.*[a-zA-Z])[a-zA-Z0-9]+$', creds["username"])):
        return 2

    # Check it is a vald password
    if len(creds["password"]) < 6:
        return 3
    elif not bool(re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)', creds["password"])):
        return 3
    elif bool(re.match(r'[ ]+', creds["password"])):
        return 3

    return 0
    
def db_execute(path, query, params = ()):
    """Script to communicate with SQL database"""

    # Establish connection
    with sqlite3.connect(path) as conn:

        # Open cursor
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Execute query
            cursor.execute(query, params)
            
            # Check if it is a SELECT
            results = None
            if query.strip().lower().startswith("select"):
                results = [dict(row) for row in cursor.fetchall()]
            else:
                conn.commit()
        except sqlite3.Error as e:
            print(f"An error reading db occurred: {e}")
            raise e
        
        # Close the connection
        cursor.close()

        return results

def refresh_activities(user_id, DB_PATH = "strava_app.db", refresh_all = False):

    # Connect to strava
    strava = Strava()

    # Get credentials
    creds = db_execute(DB_PATH, "SELECT access_key, refresh_key, key_expires FROM users WHERE id = ?", (user_id,))[0]

    # Request all activities
    index = 0
    activities = []
    while True:
        try:
            activities.extend(strava.get_activities_new(page = index, creds = creds))
        except Exception as e:
            print(f"Exiting activity refresh on loop {index} - error message {e}")
            break
        index += 1

    # Get all IDs from the current activities db
    activity_ids = [row['id'] for row in db_execute(DB_PATH, "SELECT id FROM activities")]

    # Loop through rows and add them to the db
    for row in activities:

        # Check if the activity id is already in the database, in which case skip
        if row['id'] in activity_ids:
            continue

        # Add the athlete id
        row['athlete_id'] = user_id

        # Otherwise, insert into the db
        stmt_keys = ', '.join([key for key in row.keys()])
        stmt_queries = ('?,' * len(row.keys()))[:-1]
        stmt_args = tuple(list(row.values()))

        # Execute the query
        db_execute(DB_PATH, f"INSERT INTO activities ({stmt_keys}) VALUES ({stmt_queries})", params=stmt_args)

def strava_authenticate():

    # Initialize Strava
    strava = Strava()

    # This information is obtained upon registration of a new GitHub
    client_id = strava.client_id
    client_secret = strava.secret
    auth_base_url = 'https://www.strava.com/oauth/authorize'
    redirect_url = 'http://127.0.0.1:5000/authorise'
    scope = ["profile:read_all"]

    # Create session variable
    session = OAuth2Session(client_id=client_id, redirect_uri=redirect_url, scope = scope)

    # Get auth link
    auth_link = session.authorization_url(auth_base_url)

    return auth_link[0]

def strava_exchange():

    # Initialize Strava
    strava = Strava()

    # 
    client_id = strava.client_id
    client_secret = strava.secret


    

