from functools import wraps
from flask import redirect, render_template, request, session
import re
from db_utils import db_execute
from dotenv import load_dotenv
import os

def apology(error):
    """Return apology page in case of error"""

    return render_template("apology.html", feedback = error)


def login_required(f):
    """Wrap function to ensure user is logged in to access it"""

    @wraps(f)
    def wrapped_func(* args, ** kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(* args, ** kwargs)

    return wrapped_func


def validate_credentials(creds):
    """Ensure user registration credentials provided are valid"""

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