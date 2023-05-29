from flask_sqlalchemy import SQLAlchemy
from flask import Flask


users = SQLAlchemy()

def initialize_app(database_uri):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    users.init_app(app)
    return app

