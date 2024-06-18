from functools import wraps
from flask import redirect, render_template, request, session
import re
from db_utils import db_execute
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import os

# Get db path
load_dotenv()
DB_PATH = os.getenv('DB_PATH')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

def apology(error):
    """Return apology page in case of error"""

    return render_template("apology.html", feedback = error)


def login_required(f):
    """Wrap function to ensure user is logged in to access it"""

    @wraps(f)
    def wrapped_func(* args, ** kwargs):
        if session.get("user_id") is None: # Check there is a session id
            return redirect("/login")
        elif len(db_execute(DB_PATH, "SELECT * FROM users WHERE id = ?", (session.get("user_id"),))) == 0:
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


def generate_encryption_key():
    """Generates a new encryption key - one time use"""
    
    # Generate key
    key = Fernet.generate_key()

    # Optionally, write the key to a file (for backup purposes)
    with open("secret.key", "wb") as key_file:
        key_file.write(key)
        
        
def encrypt_message(message):
    """Encrypts a message"""
    cipher_suite = Fernet(ENCRYPTION_KEY)
    encrypted_message = cipher_suite.encrypt(message.encode())
    return encrypted_message


def decrypt_message(message):
    """Encrypts a message"""
    cipher_suite = Fernet(ENCRYPTION_KEY)
    decrypted_message = cipher_suite.decrypt(message)
    return decrypted_message.decode()