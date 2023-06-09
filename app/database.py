from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_wtf import CSRFProtect

users = SQLAlchemy()


def initialize_app(database_uri):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    users.init_app(app)

    return app

