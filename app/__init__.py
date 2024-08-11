from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import secrets
from flask_migrate import Migrate
import logging
import os
from flask_mail import Mail, Message
# from flask_oauthlib.client import OAuth
# Create and configure logger
logging.basicConfig(filename="app.log", format="%(asctime)s %(message)s", filemode="w")

# Creating an object
logger = logging.getLogger()

# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)

app = Flask(__name__)

# Secret key generation
secret_key = os.getenv("SECRET_KEY")
db_url = os.getenv("DB_URL")
app.config["SECRET_KEY"] = secret_key

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configuration settings for Flask-Mail with Gmail
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv(
    "EMAIL_ADDRESS"
)  # Replace with your Gmail address
app.config["MAIL_PASSWORD"] = os.getenv(
    "EMAIL_PASSWORD"
)  # Replace with your Gmail password
app.config["MAIL_DEFAULT_SENDER"] = os.getenv(
    "EMAIL_ADDRESS"
)  # Replace with your Gmail address

# oauth = OAuth(app)
# google = oauth.remote_app(
#     'google',
#     consumer_key='YOUR_CLIENT_ID',
#     consumer_secret='YOUR_CLIENT_SECRET',
#     request_token_params={
#         'scope': 'email profile',
#     },
#     base_url='https://www.googleapis.com/oauth2/v1/',
#     request_token_url=None,
#     access_token_method='POST',
#     access_token_url='https://accounts.google.com/o/oauth2/token',
#     authorize_url='https://accounts.google.com/o/oauth2/auth',
# )


db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)

from app.routes import home

app.register_blueprint(home)
