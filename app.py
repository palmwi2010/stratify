from flask import Flask, flash, get_flashed_messages, render_template, redirect, request, session
from flask_session import Session
from flask_bcrypt import Bcrypt

from db_utils import db_init, db_execute
from helpers import login_required, validate_credentials, apology
from strava import Strava
import requests
import math

# Configure application
app = Flask(__name__)
app.debug = False

# Configure system to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize bcrypt for password hashing and set up database connection
bcrypt = Bcrypt(app)
DB_PATH = "strava_app.db"
db_init()
strava = Strava()
activities = []

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

    # If user clicks refresh, refresh the activities
    if request.method == "POST":
        if request.form.get('refresh') == "1":
            strava.refresh_activities(session['user_id'], DB_PATH=DB_PATH)

    # Get the results from SQL
    activities = db_execute(DB_PATH, "SELECT * FROM activities WHERE athlete_id = ?;", params = (session['user_id'],))

    return render_template("index.html", activities = activities)


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

    # Check for an authorisation link
    auth_code = request.args.get('code','')
    err_msg = request.args.get('error', '')

    # If auth code does not equal '':
    if auth_code != '':

        # We can now submit post request for new access
        results = strava.exchange(auth_code)

        # If results successfully returned, update the users table and redirect to home
        if results != []:
            db_execute(DB_PATH, "UPDATE users SET access_key = ?, refresh_key = ?, key_expires = ?", 
                (results['access_token'], results['refresh_token'], results['expires_at']))
            return redirect('/')

    if err_msg != '':
        return apology(err_msg)

    # Get url for strava authentication
    auth_url = strava.authenticate(request.base_url)

    # Render template for authorisation
    return render_template("authorise.html", auth_url = auth_url)