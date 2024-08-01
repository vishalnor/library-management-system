from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import secrets
from flask_migrate import Migrate
import logging
import os

# Create and configure logger
logging.basicConfig(filename="app.log", format="%(asctime)s %(message)s", filemode="w")

# Creating an object
logger = logging.getLogger()

# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)

app = Flask(__name__)

# Secret key generation
secret_key = os.getenv("SECRET_KEY")
app.config["SECRET_KEY"] = secret_key

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+mysqlconnector://avnadmin:AVNS_TYZK1N-Eu7TbZ9LsGPi@mysql-35c3371f-bhavinnor13-9cbc.l.aivencloud.com:17109/defaultdb"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)

from app.routes import home

app.register_blueprint(home)
