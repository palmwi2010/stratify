from flask import Flask, flash, get_flashed_messages, render_template, redirect, request, session
from flask_session import Session
from flask_bcrypt import Bcrypt

from db_utils import db_init, db_execute
from helpers import login_required, validate_credentials, apology, encrypt_message, decrypt_message
from engine import ChatEngine
from strava import Strava
import requests
import math
from dotenv import load_dotenv
import os

# Run command
# waitress-serve --listen=127.0.0.1:5000 app:app

# Configure application
app = Flask(__name__)
app.debug = False

# Configure system to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize bcrypt for password hashing and set up database connection
bcrypt = Bcrypt(app)
load_dotenv()
DB_PATH = os.getenv('DB_PATH')
db_init()
strava = Strava()
engine = None

# Ensure no caching of responses
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods = ["GET", "POST"])
@login_required
def index():

    # Check they have a valid access key
    try:
        access_key = db_execute(DB_PATH, "SELECT access_key FROM users WHERE id = ?;", params=(session["user_id"],))[0]['access_key']
    except:
        return apology('Could not find user id in database records.')
    
    if access_key is None:
        return redirect("/authorise")

    # Assume no activity refresh
    refreshed = False

    # If user clicks refresh, refresh the activities
    if request.method == "POST":
        if request.form.get('refresh') == "1":
            strava.refresh_activities(session['user_id'], DB_PATH=DB_PATH)
            refreshed = True

    # Get the results from SQL
    activities = db_execute(DB_PATH, "SELECT * FROM activities WHERE athlete_id = ? ORDER BY date_sort DESC;", params = (session['user_id'],))

    return render_template("index.html", activities = activities, refreshed = refreshed)

@app.route("/coach", methods = ["GET", "POST"])
@login_required
def coach():
    
    # Check they have a valid access key
    try:
        access_key = db_execute(DB_PATH, "SELECT access_key FROM users WHERE id = ?;", params=(session["user_id"],))[0]['access_key']
    except:
        return apology('Could not find user id in database records.')
    
    if access_key is None:
        return redirect("/authorise")
    
    # Get user image
    result = db_execute(DB_PATH, "SELECT profile_img FROM users WHERE id = ?", params=(session["user_id"],))
    if len(result) > 0:
        user_img = result[0]['profile_img']
    else:
        print("Warning: Could not find user in row")
        user_img = "static/media/athlete.png"

    # If it's a POST, the user has submitted a message
    if request.method == 'POST':
        
        # Use global engine
        global engine
                
        # Check if the user reset
        if request.form.get("refresh") == "Yes":
            if engine is not None:
                engine.reset_chat()
                return render_template("coach.html", user_img = user_img)
        
        # Get the user prompt
        prompt = request.form.get('prompt')
        
        if prompt != "":
            # Fire up the chat engine if it's not already running
            if engine is None:
                engine = ChatEngine()
                
            # Get activities and submit for response
            activities = db_execute(DB_PATH, "SELECT * FROM activities WHERE athlete_id = ? ORDER BY date_sort DESC;", params = (session['user_id'],))
            response = engine.generate_response(question=prompt, activities = activities)
            chat_length = len(engine.conversation_history)
            print(f"Response: {response}")
            
            # Render template with the response
            return render_template("coach.html", response = response, conversation_history = engine.conversation_history, chat_length = chat_length, user_img=user_img)

    # Clear any prior chats
    if engine is not None:
        engine.reset_chat()

    return render_template("coach.html", user_img=user_img)


@app.route("/login", methods = ["GET", "POST"])
def login():

    # Clear user id
    session.clear()

    if request.method == "POST":

        # Get username and password
        username = request.form.get("input_username")
        password = request.form.get("input_password")

        # Check for valid inputs
        if len(username) < 6:
            return render_template("login.html", feedback = "Invalid username")
        elif len(password) < 6:
            return render_template("login.html", feedback = "Invalid password")

        # Check results
        results = db_execute(DB_PATH, "SELECT * FROM users WHERE username = ?;", params=(username,))

        # Check for only one result
        if len(results) == 0:
            return render_template("login.html", feedback = "Username not found")
        elif len(results) > 1:
            return apology("More than one username found")

        # Check password
        if not bcrypt.check_password_hash(results[0]["password_hash"], password):
            return render_template("login.html", feedback = "Incorrect password. Please try again.")

        # Update session id and login
        session["user_id"] = results[0]["id"]

        # Verify if the user has already authenticated with Strava
        if results[0]['access_key'] is None:
            return redirect("/authorise")
        else:
            return redirect("/")
    else:
        return render_template("login.html")

@app.route("/register", methods = ["GET", "POST"])
def register():

    if request.method == "POST":
        
        # Handle information
        creds = {}
        creds["email"] = request.form.get('input_email')
        creds["username"] = request.form.get('input_username')
        creds["password"] = request.form.get('input_password')

        # Check for validity
        check = validate_credentials(creds)

        # Check username doesn't already exist
        if len(db_execute(DB_PATH, "SELECT * FROM users WHERE username = ?", (creds["username"],))) > 0:
            check = 4

        # Check email doesn't already exist
        if len(db_execute(DB_PATH, "SELECT * FROM users WHERE email = ?", (creds["email"],))) > 0:
            check = 5

        # If check fails, return to register page with relevant feedback
        if check != 0:
            return render_template("register.html", feedback = check)

        # Hash the password
        hash = bcrypt.generate_password_hash(creds["password"]).decode('utf-8')

        # Update database
        db_execute(DB_PATH, "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?);",
         params=(creds["username"], creds["email"], hash))

        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    # Clear session and redirect
    session.clear()
    return redirect("/")


@app.route("/authorise", methods = ["GET", "POST"])
def authorise():

    # If it's been Posted, it's a deathorisation
    if request.method == "POST":
        if request.form.get("deauthorise") == 'deauthorise':
            strava.deauthorise(session["user_id"], DB_PATH=DB_PATH)
            return redirect ("/")

    # Check if already authorised
    try:
        access_key = db_execute(DB_PATH, "SELECT access_key FROM users WHERE id = ?;", params=(session["user_id"],))[0]['access_key']
    except:
        return apology("Could not find user id in database records.")
    
    # If they already have an access key, redirect
    if access_key is not None:
        return render_template("authorise.html", auth_url = "", authorised = True)
    
    # Check for an authorisation link
    auth_code = request.args.get('code','')
    err_msg = request.args.get('error', '')

    # If auth code does not equal '':
    if auth_code != '':

        # We can now submit post request for new access
        results = strava.exchange(auth_code)
        
        # Get user image with default if not found
        user_img = results['athlete'].get("profile_medium","static/media/athlete.png")

        # If results successfully returned, update the users table and redirect to home
        if results != []:
            db_execute(DB_PATH, "UPDATE users SET profile_img = ?, access_key = ?, refresh_key = ?, key_expires = ?", 
                (user_img,encrypt_message(results['access_token']), encrypt_message(results['refresh_token']), results['expires_at']))
            return redirect('/')

    if err_msg != '':
        return apology(err_msg)

    # Get url for strava authentication
    redirect_uri = request.url_root +"/authorise"
    auth_url = strava.authenticate(redirect_uri)

    # Render template for authorisation
    return render_template("authorise.html", auth_url = auth_url, authorised = False)