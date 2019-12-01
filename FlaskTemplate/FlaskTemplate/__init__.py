"""
The flask application package.
"""
from flask_sqlalchemy import SQLAlchemy 
from flask import Flask
from flask_mail import Mail
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
lm = LoginManager()
lm.init_app(app)



import FlaskTemplate.views
