# Stratify

## About
Stratify is a web app that allows users to see analytics about their Strava activity data and speak to a chatbot 'coach', who can answer questions informed by the user's own activities. This project was developed as a final project to CS50 (Introduction to Computer Science). Stratify is hosted via Render [here](https://stratify.onrender.com/). Users can register and connect to their Strava accounts.

Stratify is built using Python, Flask and SQL for the backend. On the front-end, JS frameworks used include Bootstrap, DataTables and Google Charts. Stratify uses Strava's API to authenticate users (via OAuth2) and request activity data. Stratify also uses OpenAI's API with gpt-3.5-turbo for the chatbot coach.

## Running Stratify
In order to run Stratify yourself, you can clone the repository and install all package requirements found in `requirements.txt`. You will also need to obtain access tokens for both Strava and OpenAI to use these APIs, and store them in a `.env` file. This config file has the following format:
```
{
    "CLIENT_SECRET": Strava API client secret
    "CLIENT_ID": Strava API client ID
    "DB_PATH": Path to a .db file used
    "ENCRYPTION_KEY": Encryption key for token encryption (from cryptography.fernet)
    "OPENAI_KEY": API key for OpenAI
}
```
To run Stratify locally, you can use `flask run` to run using localhost. Once deployed, I use Waitress in order to host Stratify. Waitress can be called using `waitress-serve --listen=127.0.0.1:5000 app:app` (example for localhost).

## Possible extensions
The main extensions to Stratify could involve:
* More detailed analytics on activities data
* Ability to deep-dive on individual activities
* Training plan with a calendar view
* Live connection with Strava using webhooks